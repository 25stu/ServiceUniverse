from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from sqlalchemy import case, create_engine, select
from sqlalchemy.orm import sessionmaker

from services.parking_billing.app.models import (
    Base,
    ParkingPayment,
    ParkingSession,
    ProcessEvent,
)
from services.parking_billing.app.services import calculate_parking_fee

DEFAULT_DATABASE_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "parking_billing.db"
)


def as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


class BillingRepository:
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

    @staticmethod
    def _event(
        parking_session: ParkingSession,
        activity: str,
        status: str,
        *,
        cost_minor: int | None = None,
        duration_seconds: int | None = None,
    ) -> ProcessEvent:
        return ProcessEvent(
            event_id=str(uuid4()),
            case_id=parking_session.session_id,
            activity=activity,
            timestamp=datetime.now(UTC),
            resource="parking-billing-service",
            lifecycle="complete",
            outcome="success",
            service="parking-billing",
            citizen_id=parking_session.citizen_id,
            cost_minor=cost_minor,
            duration_seconds=duration_seconds,
            status=status,
        )

    def create_session(
        self,
        citizen_id: str,
        vehicle_plate: str,
        parking_lot_id: str,
        started_at: datetime | None,
    ) -> tuple[ParkingSession | None, str | None]:
        with self.session_factory() as database:
            active = database.scalar(
                select(ParkingSession).where(
                    ParkingSession.vehicle_plate == vehicle_plate,
                    ParkingSession.status == "active",
                )
            )
            if active is not None:
                return None, "ACTIVE_SESSION_EXISTS"
            parking_session = ParkingSession(
                session_id=str(uuid4()),
                citizen_id=citizen_id,
                vehicle_plate=vehicle_plate,
                parking_lot_id=parking_lot_id,
                started_at=started_at or datetime.now(UTC),
                ended_at=None,
                duration_minutes=None,
                amount_minor=None,
                currency="AUD",
                status="active",
                payment_status="not_due",
            )
            database.add(parking_session)
            database.add(
                self._event(parking_session, "Register Parking Entry", "active")
            )
            database.commit()
            database.refresh(parking_session)
            database.expunge(parking_session)
            return parking_session, None

    def list_sessions(
        self, citizen_id: str | None = None, status: str | None = None
    ) -> list[ParkingSession]:
        query = select(ParkingSession)
        if citizen_id:
            query = query.where(ParkingSession.citizen_id == citizen_id)
        if status:
            query = query.where(ParkingSession.status == status)
        query = query.order_by(ParkingSession.started_at.desc())
        with self.session_factory() as database:
            return list(database.scalars(query))

    def get_session(self, session_id: str) -> ParkingSession | None:
        with self.session_factory() as database:
            return database.get(ParkingSession, session_id)

    def end_session(
        self, session_id: str, ended_at: datetime | None
    ) -> tuple[ParkingSession | None, str | None]:
        with self.session_factory() as database:
            parking_session = database.get(ParkingSession, session_id)
            if parking_session is None:
                return None, "PARKING_SESSION_NOT_FOUND"
            if parking_session.status != "active":
                return parking_session, "SESSION_ALREADY_ENDED"
            normalized_start = as_utc(parking_session.started_at)
            normalized_end = as_utc(ended_at or datetime.now(UTC))
            try:
                duration_minutes, amount_minor = calculate_parking_fee(
                    normalized_start, normalized_end
                )
            except ValueError:
                return parking_session, "INVALID_END_TIME"
            parking_session.ended_at = normalized_end
            parking_session.duration_minutes = duration_minutes
            parking_session.amount_minor = amount_minor
            parking_session.status = "completed"
            parking_session.payment_status = "unpaid"
            database.add(
                self._event(
                    parking_session,
                    "Close Parking Session",
                    "completed",
                    duration_seconds=duration_minutes * 60,
                )
            )
            database.add(
                self._event(
                    parking_session,
                    "Calculate Parking Fee",
                    "unpaid",
                    cost_minor=amount_minor,
                    duration_seconds=duration_minutes * 60,
                )
            )
            database.commit()
            database.refresh(parking_session)
            database.expunge(parking_session)
            return parking_session, None

    def create_payment(
        self, session_id: str, payment_method: str
    ) -> tuple[ParkingPayment | None, str | None]:
        with self.session_factory() as database:
            parking_session = database.get(ParkingSession, session_id)
            if parking_session is None:
                return None, "PARKING_SESSION_NOT_FOUND"
            if parking_session.status != "completed":
                return None, "SESSION_NOT_BILLABLE"
            if parking_session.payment_status == "paid":
                return None, "SESSION_ALREADY_PAID"
            assert parking_session.amount_minor is not None
            database.add(
                self._event(
                    parking_session,
                    "Initiate Payment",
                    "processing",
                    cost_minor=parking_session.amount_minor,
                )
            )
            payment = ParkingPayment(
                payment_id=str(uuid4()),
                session_id=parking_session.session_id,
                amount_minor=parking_session.amount_minor,
                currency=parking_session.currency,
                payment_method=payment_method,
                status="completed",
                paid_at=datetime.now(UTC),
            )
            parking_session.payment_status = "paid"
            database.add(payment)
            database.add(
                self._event(
                    parking_session,
                    "Confirm Payment",
                    "paid",
                    cost_minor=parking_session.amount_minor,
                )
            )
            database.commit()
            database.refresh(payment)
            database.expunge(payment)
            return payment, None

    def get_payment(self, payment_id: str) -> ParkingPayment | None:
        with self.session_factory() as database:
            return database.get(ParkingPayment, payment_id)

    def list_events(self, session_id: str) -> list[ProcessEvent] | None:
        with self.session_factory() as database:
            parking_session = database.get(ParkingSession, session_id)
            if parking_session is None:
                return None
            return list(
                database.scalars(
                    select(ProcessEvent)
                    .where(ProcessEvent.case_id == session_id)
                    .order_by(
                        ProcessEvent.timestamp,
                        case(
                            {
                                "Register Parking Entry": 1,
                                "Close Parking Session": 2,
                                "Calculate Parking Fee": 3,
                                "Initiate Payment": 4,
                                "Confirm Payment": 5,
                                "Reject Payment": 5,
                            },
                            value=ProcessEvent.activity,
                            else_=99,
                        ),
                        ProcessEvent.event_id,
                    )
                )
            )
