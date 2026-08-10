from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

REQUIRED_COLUMNS = {
    "case_id",
    "activity",
    "timestamp",
    "resource",
    "lifecycle",
    "outcome",
}
OPTIONAL_COLUMNS = {
    "service",
    "citizen_id",
    "cost_minor",
    "duration_seconds",
    "status",
}
TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S%z"


def load_and_validate(input_path: Path) -> pd.DataFrame:
    event_log = pd.read_csv(input_path)
    missing = REQUIRED_COLUMNS - set(event_log.columns)
    if missing:
        missing_list = ", ".join(sorted(missing))
        raise ValueError(f"Missing required columns: {missing_list}")

    event_log = event_log.copy()
    event_log["timestamp"] = pd.to_datetime(event_log["timestamp"], utc=True)
    if event_log[["case_id", "activity", "timestamp"]].isna().any().any():
        raise ValueError("case_id, activity, and timestamp must not be empty")

    event_log = event_log.sort_values(["case_id", "timestamp", "activity"])
    return event_log


def build_summary(event_log: pd.DataFrame) -> dict[str, Any]:
    grouped = event_log.groupby("case_id", sort=False)
    variants = (
        grouped["activity"]
        .apply(lambda values: " -> ".join(values.astype(str)))
        .value_counts()
        .rename_axis("variant")
        .reset_index(name="case_count")
    )

    case_durations = grouped["timestamp"].agg(["min", "max"])
    duration_seconds = (
        case_durations["max"] - case_durations["min"]
    ).dt.total_seconds()

    summary: dict[str, Any] = {
        "case_count": int(grouped.ngroups),
        "event_count": int(len(event_log)),
        "activity_count": int(event_log["activity"].nunique()),
        "activities": sorted(event_log["activity"].dropna().unique().tolist()),
        "outcomes": event_log["outcome"].value_counts().to_dict(),
        "variants": variants.head(10).to_dict(orient="records"),
        "duration_seconds": {
            "min": float(duration_seconds.min()),
            "median": float(duration_seconds.median()),
            "max": float(duration_seconds.max()),
        },
    }
    return summary


def write_outputs(event_log: pd.DataFrame, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    cleaned_path = output_dir / "parking_billing_cleaned.csv"
    summary_path = output_dir / "parking_billing_summary.json"

    event_log.to_csv(cleaned_path, index=False)
    summary = build_summary(event_log)
    summary_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate, clean, and summarize Parking Billing event logs."
    )
    parser.add_argument(
        "input_csv",
        type=Path,
        help="Raw Parking Billing CSV exported or simulated by Member E.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("analytics/parking_billing/results"),
        help="Directory for cleaned CSV and summary JSON outputs.",
    )
    args = parser.parse_args()

    event_log = load_and_validate(args.input_csv)
    write_outputs(event_log, args.output_dir)
    print(f"Validated {len(event_log)} events from {args.input_csv}")
    print(f"Wrote cleaned log and summary to {args.output_dir}")


if __name__ == "__main__":
    main()
