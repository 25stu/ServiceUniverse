from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


def ensure_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


class ParkingSessionCreate(BaseModel):
    citizen_id: str = Field(min_length=1, max_length=80)
    vehicle_plate: str = Field(min_length=2, max_length=12, pattern=r"^[A-Za-z0-9 -]+$")
    parking_lot_id: str = Field(min_length=1, max_length=32)
    started_at: datetime | None = None

    @field_validator("vehicle_plate")
    @classmethod
    def normalize_plate(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("started_at")
    @classmethod
    def normalize_started_at(cls, value: datetime | None) -> datetime | None:
        return ensure_utc(value)


class ParkingSessionEnd(BaseModel):
    ended_at: datetime | None = None

    @field_validator("ended_at")
    @classmethod
    def normalize_ended_at(cls, value: datetime | None) -> datetime | None:
        return ensure_utc(value)


class ParkingPaymentCreate(BaseModel):
    session_id: str = Field(min_length=1, max_length=40)
    payment_method: Literal["card", "digital_wallet"]


class ParkingSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    session_id: str
    citizen_id: str
    vehicle_plate: str
    parking_lot_id: str
    started_at: datetime
    ended_at: datetime | None
    duration_minutes: int | None
    amount_minor: int | None
    currency: str
    status: Literal["active", "completed"]
    payment_status: Literal["not_due", "unpaid", "paid"]

    @field_validator("started_at", "ended_at", mode="before")
    @classmethod
    def add_timezone(cls, value: datetime | None) -> datetime | None:
        return ensure_utc(value)


class ParkingPaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    payment_id: str
    session_id: str
    amount_minor: int
    currency: str
    payment_method: Literal["card", "digital_wallet"]
    status: Literal["completed"]
    paid_at: datetime

    @field_validator("paid_at", mode="before")
    @classmethod
    def add_timezone(cls, value: datetime) -> datetime:
        normalized = ensure_utc(value)
        assert normalized is not None
        return normalized


class ProcessEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    case_id: str
    activity: str
    timestamp: datetime
    resource: str
    lifecycle: str
    outcome: str
    service: str
    citizen_id: str
    cost_minor: int | None
    duration_seconds: int | None
    status: str

    @field_validator("timestamp", mode="before")
    @classmethod
    def add_timezone(cls, value: datetime) -> datetime:
        normalized = ensure_utc(value)
        assert normalized is not None
        return normalized
