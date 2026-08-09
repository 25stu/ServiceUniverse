from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from services.parking_availability.app.models import Base, ParkingLot

DEFAULT_DATABASE_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "parking_availability.db"
)

SEED_PARKING_LOTS = (
    {
        "lot_id": "LOT-CENTRAL-001",
        "name": "Central Station Car Park",
        "address": "18 Railway Square",
        "total_spaces": 240,
        "available_spaces": 64,
        "accessible_spaces": 12,
    },
    {
        "lot_id": "LOT-HARBOUR-002",
        "name": "Harbour Public Parking",
        "address": "7 Waterfront Drive",
        "total_spaces": 180,
        "available_spaces": 18,
        "accessible_spaces": 8,
    },
    {
        "lot_id": "LOT-LIBRARY-003",
        "name": "Civic Library Car Park",
        "address": "42 Knowledge Street",
        "total_spaces": 96,
        "available_spaces": 0,
        "accessible_spaces": 6,
    },
)


class ParkingLotRepository:
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
        with self.session_factory() as session:
            if session.scalar(select(ParkingLot.lot_id).limit(1)) is None:
                now = datetime.now(UTC)
                session.add_all(
                    ParkingLot(**parking_lot, updated_at=now)
                    for parking_lot in SEED_PARKING_LOTS
                )
                session.commit()

    def list_parking_lots(self) -> list[ParkingLot]:
        with self.session_factory() as session:
            return list(session.scalars(select(ParkingLot).order_by(ParkingLot.name)))

    def get_parking_lot(self, lot_id: str) -> ParkingLot | None:
        with self.session_factory() as session:
            return session.get(ParkingLot, lot_id)

    def update_availability(
        self, lot_id: str, available_spaces: int
    ) -> tuple[ParkingLot | None, bool]:
        with self.session_factory() as session:
            parking_lot = session.get(ParkingLot, lot_id)
            if parking_lot is None:
                return None, False
            if available_spaces > parking_lot.total_spaces:
                return parking_lot, False
            parking_lot.available_spaces = available_spaces
            parking_lot.updated_at = datetime.now(UTC)
            session.commit()
            session.refresh(parking_lot)
            session.expunge(parking_lot)
            return parking_lot, True
