from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class BillResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    bill_id: str
    citizen_id: str
    account_reference: str
    description: str
    issued_on: date
    due_on: date
    amount_minor: int = Field(ge=0)
    currency: str
    status: Literal["unpaid", "paid"]
    paid_at: datetime | None


class BillDetailResponse(BillResponse):
    customer_name: str
    service_address: str
    meter_number: str
    billing_period_start: date
    billing_period_end: date
    previous_meter_reading: int
    current_meter_reading: int
    water_usage_kl: int = Field(ge=0)
    fixed_charge_minor: int = Field(ge=0)
    consumption_charge_minor: int = Field(ge=0)
    gst_minor: int = Field(ge=0)


class PaymentCreate(BaseModel):
    bill_id: str = Field(pattern=r"^BILL-[A-Z0-9-]+$")
    payment_method: Literal["card", "bank_transfer"]


class PaymentReceipt(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    payment_id: str
    bill_id: str
    citizen_id: str
    amount_minor: int = Field(ge=0)
    currency: str
    payment_method: Literal["card", "bank_transfer"]
    status: Literal["completed"]
    paid_at: datetime
    receipt_number: str
