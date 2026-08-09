from __future__ import annotations

from datetime import datetime
from math import ceil

HOURLY_RATE_MINOR = 400
DAILY_CAP_MINOR = 4000


def calculate_parking_fee(started_at: datetime, ended_at: datetime) -> tuple[int, int]:
    duration_seconds = int((ended_at - started_at).total_seconds())
    if duration_seconds <= 0:
        raise ValueError("The parking session end time must be after its start time.")
    duration_minutes = max(1, ceil(duration_seconds / 60))
    billed_hours = ceil(duration_minutes / 60)
    amount_minor = min(billed_hours * HOURLY_RATE_MINOR, DAILY_CAP_MINOR)
    return duration_minutes, amount_minor
