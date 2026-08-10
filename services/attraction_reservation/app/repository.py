from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from services.attraction_reservation.app.models import Base, ReservationRecord

DEFAULT_DATABASE_PATH = (
    Path(__file__).resolve().parents[1] / "data" / "attraction_reservation.db"
)


class ReservationRepository:
    def __init__(self, database_url: str | None = None) -> None:
        resolved_url = database_url or f"sqlite:///{DEFAULT_DATABASE_PATH.as_posix()}"
        if resolved_url.startswith("sqlite:///"):
            database_path = resolved_url.removeprefix("sqlite:///")
            if database_path != ":memory:":
                Path(database_path).parent.mkdir(parents=True, exist_ok=True)
        self.engine = create_engine(
            resolved_url,
            connect_args={"check_same_thread": False}
            if resolved_url.startswith("sqlite")
            else {},
        )
        self.session_factory = sessionmaker(self.engine, expire_on_commit=False)

    def initialize(self) -> None:
        Base.metadata.create_all(self.engine)

    def reserved_visitors(self, attraction_id: str, visit_date: date) -> int:
        with self.session_factory() as session:
            total = session.scalar(
                select(func.coalesce(func.sum(ReservationRecord.visitor_count), 0))
                .where(ReservationRecord.attraction_id == attraction_id)
                .where(ReservationRecord.visit_date == visit_date)
                .where(ReservationRecord.status.in_(("pending", "confirmed")))
            )
            return int(total or 0)

    def create(self, values: dict[str, Any]) -> ReservationRecord:
        with self.session_factory() as session:
            reservation = ReservationRecord(**values)
            session.add(reservation)
            session.commit()
            session.refresh(reservation)
            session.expunge(reservation)
            return reservation

    def get(self, reservation_id: str) -> ReservationRecord | None:
        with self.session_factory() as session:
            reservation = session.get(ReservationRecord, reservation_id)
            if reservation is not None:
                session.expunge(reservation)
            return reservation

    def update_status(
        self, reservation_id: str, status: str
    ) -> ReservationRecord | None:
        with self.session_factory() as session:
            reservation = session.get(ReservationRecord, reservation_id)
            if reservation is None:
                return None
            reservation.status = status
            session.commit()
            session.refresh(reservation)
            session.expunge(reservation)
            return reservation
