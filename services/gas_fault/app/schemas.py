from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints, field_validator

ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2)]


class Severity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FaultStatus(StrEnum):
    REPORTED = "reported"
    ASSIGNED = "assigned"
    INSPECTION_IN_PROGRESS = "inspection_in_progress"
    REPAIR_IN_PROGRESS = "repair_in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class FaultReportCreate(BaseModel):
    citizen_id: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True,
            min_length=3,
            max_length=64,
            pattern=r"^[A-Za-z0-9_-]+$",
        ),
    ]
    reporter_name: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=2, max_length=100)
    ]
    contact_phone: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True,
            min_length=7,
            max_length=24,
            pattern=r"^[0-9+() -]+$",
        ),
    ]
    address: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=5, max_length=200)
    ]
    description: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=10, max_length=1000),
    ]
    severity: Severity

    @field_validator("reporter_name", "address", "description")
    @classmethod
    def reject_blank_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must contain visible characters")
        return value


class FaultStatusUpdate(BaseModel):
    status: FaultStatus
    resource: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=2, max_length=100)
    ]
    note: Annotated[
        str | None,
        StringConstraints(strip_whitespace=True, max_length=500),
    ] = None


class FaultStatusHistory(BaseModel):
    status: FaultStatus
    activity: str
    resource: str
    note: str | None
    timestamp: str


class FaultReport(BaseModel):
    report_id: str
    citizen_id: str
    reporter_name: str
    contact_phone: str
    address: str
    description: str
    severity: Severity
    status: FaultStatus
    created_at: str
    updated_at: str
    history: list[FaultStatusHistory] = Field(default_factory=list)
