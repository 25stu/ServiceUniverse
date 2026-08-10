from pathlib import Path

from analytics.parking_billing.mining.analyze_parking_billing import (
    build_summary,
    load_and_validate,
)


def test_parking_billing_log_validation_and_summary(tmp_path: Path) -> None:
    raw_log = tmp_path / "parking_billing.csv"
    rows = [
        ["case_id", "activity", "timestamp", "resource", "lifecycle", "outcome"],
        [
            "PB-1",
            "Start parking session",
            "2026-08-05T09:00:00+10:00",
            "system",
            "complete",
            "success",
        ],
        [
            "PB-1",
            "End parking session",
            "2026-08-05T10:00:00+10:00",
            "system",
            "complete",
            "success",
        ],
        [
            "PB-1",
            "Calculate parking fee",
            "2026-08-05T10:01:00+10:00",
            "billing",
            "complete",
            "success",
        ],
        [
            "PB-2",
            "Start parking session",
            "2026-08-05T11:00:00+10:00",
            "system",
            "complete",
            "success",
        ],
        [
            "PB-2",
            "Payment failed",
            "2026-08-05T12:00:00+10:00",
            "payment",
            "complete",
            "failed",
        ],
    ]
    raw_log.write_text(
        "\n".join(",".join(row) for row in rows),
        encoding="utf-8",
    )

    event_log = load_and_validate(raw_log)
    summary = build_summary(event_log)

    assert summary["case_count"] == 2
    assert summary["event_count"] == 5
    assert summary["activity_count"] == 4
    assert summary["outcomes"] == {"success": 4, "failed": 1}
