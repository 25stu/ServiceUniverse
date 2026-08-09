from sqlalchemy import String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class FaultReportRecord(Base):
    __tablename__ = "fault_reports"

    report_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    citizen_id: Mapped[str] = mapped_column(String(64), index=True)
    reporter_name: Mapped[str] = mapped_column(String(100))
    contact_phone: Mapped[str] = mapped_column(String(24))
    address: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(16))
    status: Mapped[str] = mapped_column(String(32), index=True)
    created_at: Mapped[str] = mapped_column(String(32))
    updated_at: Mapped[str] = mapped_column(String(32))


class FaultStatusHistoryRecord(Base):
    __tablename__ = "fault_status_history"

    event_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    report_id: Mapped[str] = mapped_column(String(32), index=True)
    status: Mapped[str] = mapped_column(String(32))
    activity: Mapped[str] = mapped_column(String(100))
    resource: Mapped[str] = mapped_column(String(100))
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    timestamp: Mapped[str] = mapped_column(String(32))
