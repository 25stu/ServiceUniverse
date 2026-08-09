from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator


class ParkingLotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    lot_id: str
    name: str
    address: str
    total_spaces: int
    available_spaces: int
    accessible_spaces: int
    updated_at: datetime

    @field_validator("updated_at", mode="before")
    @classmethod
    def add_utc_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    @computed_field
    @property
    def availability_status(self) -> Literal["available", "limited", "full"]:
        if self.available_spaces == 0:
            return "full"
        if self.available_spaces <= max(5, self.total_spaces // 10):
            return "limited"
        return "available"


class AvailabilityUpdate(BaseModel):
    available_spaces: int = Field(ge=0)
