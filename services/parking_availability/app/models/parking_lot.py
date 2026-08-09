from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ParkingLot(Base):
    __tablename__ = "parking_lots"

    lot_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    address: Mapped[str] = mapped_column(String(240), nullable=False)
    total_spaces: Mapped[int] = mapped_column(Integer, nullable=False)
    available_spaces: Mapped[int] = mapped_column(Integer, nullable=False)
    accessible_spaces: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
