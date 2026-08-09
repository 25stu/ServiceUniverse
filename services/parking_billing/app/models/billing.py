from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ParkingSession(Base):
    __tablename__ = "parking_sessions"

    session_id: Mapped[str] = mapped_column(String(40), primary_key=True)
    citizen_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    vehicle_plate: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    parking_lot_id: Mapped[str] = mapped_column(String(32), nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_minutes: Mapped[int | None] = mapped_column(Integer)
    amount_minor: Mapped[int | None] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="AUD")
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    payment_status: Mapped[str] = mapped_column(String(20), nullable=False)


class ParkingPayment(Base):
    __tablename__ = "parking_payments"

    payment_id: Mapped[str] = mapped_column(String(40), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    amount_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    payment_method: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    paid_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ProcessEvent(Base):
    __tablename__ = "parking_billing_events"

    event_id: Mapped[str] = mapped_column(String(40), primary_key=True)
    case_id: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    activity: Mapped[str] = mapped_column(String(80), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resource: Mapped[str] = mapped_column(String(80), nullable=False)
    lifecycle: Mapped[str] = mapped_column(String(20), nullable=False)
    outcome: Mapped[str] = mapped_column(String(20), nullable=False)
    service: Mapped[str] = mapped_column(String(40), nullable=False)
    citizen_id: Mapped[str] = mapped_column(String(80), nullable=False)
    cost_minor: Mapped[int | None] = mapped_column(Integer)
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
