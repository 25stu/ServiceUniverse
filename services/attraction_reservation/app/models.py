from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ReservationRecord(Base):
    __tablename__ = "attraction_reservations"

    reservation_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    attraction_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    citizen_id: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    visit_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    visitor_count: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    contact_phone: Mapped[str | None] = mapped_column(String(30))
