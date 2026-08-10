from __future__ import annotations

import re
from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PreferredLanguage(StrEnum):
    ENGLISH = "en"
    CHINESE = "zh"


class CardType(StrEnum):
    DIGITAL = "digital"
    PHYSICAL = "physical"


class AccountStatus(StrEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    RESTRICTED = "restricted"


class PaymentStatus(StrEnum):
    NOT_REQUIRED = "not_required"
    PAID = "paid"


class MembershipApplication(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    citizen_id: str = Field(
        min_length=3,
        max_length=64,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]*$",
    )
    full_name: str = Field(min_length=2, max_length=100)
    date_of_birth: date
    email: str = Field(min_length=5, max_length=254)
    phone: str = Field(min_length=7, max_length=30, pattern=r"^\+?[0-9 ()-]{7,30}$")
    preferred_language: PreferredLanguage = PreferredLanguage.ENGLISH
    card_type: CardType = CardType.DIGITAL
    home_branch: str = Field(min_length=2, max_length=100)
    mailing_address: str | None = Field(default=None, max_length=300)
    identity_verified: bool
    terms_accepted: bool
    payment_confirmed: bool

    @model_validator(mode="after")
    def validate_application(self) -> MembershipApplication:
        if self.date_of_birth > date.today():
            raise ValueError("date_of_birth must not be in the future")
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", self.email):
            raise ValueError("email must be a valid email address")
        if self.card_type is CardType.PHYSICAL and not self.mailing_address:
            raise ValueError("mailing_address is required for a physical card")
        return self


class AccountUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    email: str | None = Field(default=None, min_length=5, max_length=254)
    phone: str | None = Field(
        default=None,
        min_length=7,
        max_length=30,
        pattern=r"^\+?[0-9 ()-]{7,30}$",
    )
    preferred_language: PreferredLanguage | None = None
    home_branch: str | None = Field(default=None, min_length=2, max_length=100)
    mailing_address: str | None = Field(default=None, min_length=5, max_length=300)

    @model_validator(mode="after")
    def validate_update(self) -> AccountUpdate:
        if not any(value is not None for value in self.model_dump().values()):
            raise ValueError("at least one account field must be provided")
        if self.email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", self.email):
            raise ValueError("email must be a valid email address")
        return self


class MembershipCard(BaseModel):
    card_number: str
    card_type: CardType
    issued_at: datetime
    delivery_status: str


class BorrowingSummary(BaseModel):
    items_on_loan: int = 0
    items_overdue: int = 0
    outstanding_fees_minor: int = 0
    currency: str = "AUD"
    borrowing_allowed: bool = True


class MembershipPayment(BaseModel):
    amount_minor: int
    currency: str = "AUD"
    status: PaymentStatus
    processed_at: datetime
    payment_reference: str | None = None


class LibraryAccount(BaseModel):
    account_id: str
    citizen_id: str
    full_name: str
    date_of_birth: date
    email: str
    phone: str
    preferred_language: PreferredLanguage
    home_branch: str
    mailing_address: str | None
    status: AccountStatus
    created_at: datetime
    activated_at: datetime
    card: MembershipCard
    payment: MembershipPayment
    borrowing: BorrowingSummary
    confirmation_notification: str
