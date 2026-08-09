from __future__ import annotations

import argparse
import csv
import random
from datetime import UTC, datetime, timedelta
from pathlib import Path

FIELDNAMES = [
    "case_id",
    "activity",
    "timestamp",
    "resource",
    "lifecycle",
    "outcome",
    "service",
    "citizen_id",
    "cost_minor",
    "duration_seconds",
    "status",
    "source",
    "parking_lot_id",
    "vehicle_plate",
]

NORMAL_ACTIVITIES = (
    "Register Parking Entry",
    "Close Parking Session",
    "Calculate Parking Fee",
    "Initiate Payment",
    "Confirm Payment",
)
REJECTED_ACTIVITIES = (*NORMAL_ACTIVITIES[:-1], "Reject Payment")
ACTIVE_ACTIVITIES = ("Register Parking Entry",)


def event_rows(case_count: int, seed: int) -> list[dict[str, str | int]]:
    randomizer = random.Random(seed)
    base_time = datetime(2026, 8, 1, 7, 0, tzinfo=UTC)
    rows: list[dict[str, str | int]] = []
    lots = ("LOT-CENTRAL-001", "LOT-HARBOUR-002", "LOT-LIBRARY-003")

    for index in range(1, case_count + 1):
        case_id = f"PARK-{index:04d}"
        citizen_id = f"CITIZEN-{((index - 1) % 12) + 1:03d}"
        vehicle_plate = f"SU {index:04d}"
        parking_lot_id = lots[(index - 1) % len(lots)]
        started_at = base_time + timedelta(minutes=index * 37)
        duration_minutes = randomizer.randint(20, 360)
        amount_minor = min(((duration_minutes + 59) // 60) * 400, 4000)

        path_selector = index % 10
        if path_selector == 0:
            activities = ACTIVE_ACTIVITIES
            final_status = "active"
        elif path_selector in {7, 8}:
            activities = REJECTED_ACTIVITIES
            final_status = "payment_failed"
        else:
            activities = NORMAL_ACTIVITIES
            final_status = "paid"

        event_time = started_at
        for activity_index, activity in enumerate(activities):
            if activity == "Close Parking Session":
                event_time = started_at + timedelta(minutes=duration_minutes)
            elif activity_index > 0:
                event_time += timedelta(seconds=randomizer.randint(1, 18))
            outcome = "failure" if activity == "Reject Payment" else "success"
            status = final_status if activity == activities[-1] else "in_progress"
            rows.append(
                {
                    "case_id": case_id,
                    "activity": activity,
                    "timestamp": event_time.isoformat().replace("+00:00", "Z"),
                    "resource": "parking-billing-service",
                    "lifecycle": "complete",
                    "outcome": outcome,
                    "service": "parking-billing",
                    "citizen_id": citizen_id,
                    "cost_minor": amount_minor
                    if activity
                    in {
                        "Calculate Parking Fee",
                        "Initiate Payment",
                        "Confirm Payment",
                        "Reject Payment",
                    }
                    else "",
                    "duration_seconds": duration_minutes * 60
                    if activity in {"Close Parking Session", "Calculate Parking Fee"}
                    else "",
                    "status": status,
                    "source": "simulated",
                    "parking_lot_id": parking_lot_id,
                    "vehicle_plate": vehicle_plate,
                }
            )
    return rows


def write_event_log(output_path: Path, case_count: int, seed: int) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(event_rows(case_count, seed))


def parse_args() -> argparse.Namespace:
    default_output = (
        Path(__file__).resolve().parents[1]
        / "event_logs"
        / "parking_billing_simulated.csv"
    )
    parser = argparse.ArgumentParser(
        description="Generate deterministic simulated Parking Billing events."
    )
    parser.add_argument("--cases", type=int, default=30)
    parser.add_argument("--seed", type=int, default=927)
    parser.add_argument("--output", type=Path, default=default_output)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.cases < 1:
        raise SystemExit("--cases must be at least 1")
    write_event_log(args.output, args.cases, args.seed)
    print(f"Wrote {args.cases} simulated cases to {args.output}")


if __name__ == "__main__":
    main()
