from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Bill(Base):
    __tablename__ = "bills"

    bill_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    citizen_id: Mapped[str] = mapped_column(String(64), index=True)
    account_reference: Mapped[str] = mapped_column(String(64))
    description: Mapped[str] = mapped_column(String(160))
    issued_on: Mapped[date] = mapped_column(Date)
    due_on: Mapped[date] = mapped_column(Date)
    amount_minor: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3))
    status: Mapped[str] = mapped_column(String(16), index=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    payment: Mapped[Payment | None] = relationship(back_populates="bill")


class Payment(Base):
    __tablename__ = "payments"
    # 数据库这一层再保证一次：同一张账单只能有一条付款记录。
    __table_args__ = (UniqueConstraint("bill_id", name="uq_payment_bill_id"),)

    payment_id: Mapped[str] = mapped_column(String(48), primary_key=True)
    bill_id: Mapped[str] = mapped_column(ForeignKey("bills.bill_id"))
    citizen_id: Mapped[str] = mapped_column(String(64), index=True)
    amount_minor: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3))
    payment_method: Mapped[str] = mapped_column(String(24))
    status: Mapped[str] = mapped_column(String(16))
    paid_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    receipt_number: Mapped[str] = mapped_column(String(64), unique=True)
    bill: Mapped[Bill] = relationship(back_populates="payment")
