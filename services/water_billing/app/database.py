from __future__ import annotations

import os
from collections.abc import Generator
from datetime import UTC, date, datetime
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from services.water_billing.app.models.billing import Base, Bill, Payment

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DEFAULT_DATABASE_URL = f"sqlite:///{DATA_DIR / 'water_billing.db'}"

engine: Engine
SessionLocal: sessionmaker[Session]


def configure(database_url: str | None = None) -> None:
    """Configure the service-owned database connection."""
    global engine, SessionLocal

    url = database_url or os.getenv("WATER_DATABASE_URL", DEFAULT_DATABASE_URL)
    if url.startswith("sqlite:///"):
        # 本地跑 SQLite 时先保证数据目录存在。
        DATA_DIR.mkdir(parents=True, exist_ok=True)
    engine = create_engine(
        url,
        connect_args={"check_same_thread": False} if url.startswith("sqlite") else {},
    )
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def initialise_database() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        # 这些账单用来演示未缴、已缴和不同市民的查询结果。
        demo_bills = [
            Bill(
                bill_id="BILL-1001",
                citizen_id="CITIZEN-1001",
                account_reference="WATER-2048",
                description="Quarterly water usage",
                issued_on=date(2026, 7, 1),
                due_on=date(2026, 8, 15),
                amount_minor=12650,
                currency="AUD",
                status="unpaid",
            ),
            Bill(
                bill_id="BILL-1002",
                citizen_id="CITIZEN-1001",
                account_reference="WATER-2048",
                description="Service connection charge",
                issued_on=date(2026, 6, 1),
                due_on=date(2026, 6, 30),
                amount_minor=3800,
                currency="AUD",
                status="paid",
                paid_at=datetime(2026, 6, 12, 9, 30, tzinfo=UTC),
            ),
            Bill(
                bill_id="BILL-2001",
                citizen_id="CITIZEN-2001",
                account_reference="WATER-8831",
                description="Quarterly water usage",
                issued_on=date(2026, 7, 1),
                due_on=date(2026, 8, 15),
                amount_minor=9425,
                currency="AUD",
                status="unpaid",
            ),
            Bill(
                bill_id="BILL-2002",
                citizen_id="CITIZEN-2001",
                account_reference="WATER-8831",
                description="Quarterly water usage",
                issued_on=date(2026, 4, 1),
                due_on=date(2026, 5, 15),
                amount_minor=8860,
                currency="AUD",
                status="paid",
                paid_at=datetime(2026, 5, 10, 10, 15, tzinfo=UTC),
            ),
            Bill(
                bill_id="BILL-2003",
                citizen_id="CITIZEN-2001",
                account_reference="WATER-8831",
                description="Quarterly water usage",
                issued_on=date(2026, 1, 1),
                due_on=date(2026, 2, 15),
                amount_minor=9120,
                currency="AUD",
                status="paid",
                paid_at=datetime(2026, 2, 11, 14, 5, tzinfo=UTC),
            ),
            Bill(
                bill_id="BILL-2004",
                citizen_id="CITIZEN-2001",
                account_reference="WATER-8831",
                description="Quarterly water usage",
                issued_on=date(2026, 8, 1),
                due_on=date(2026, 9, 15),
                amount_minor=9780,
                currency="AUD",
                status="unpaid",
            ),
            Bill(
                bill_id="BILL-1003",
                citizen_id="CITIZEN-1001",
                account_reference="WATER-2048",
                description="Quarterly water usage",
                issued_on=date(2026, 4, 1),
                due_on=date(2026, 5, 15),
                amount_minor=11230,
                currency="AUD",
                status="paid",
                paid_at=datetime(2026, 5, 9, 11, 20, tzinfo=UTC),
            ),
            Bill(
                bill_id="BILL-1004",
                citizen_id="CITIZEN-1001",
                account_reference="WATER-2048",
                description="Quarterly water usage",
                issued_on=date(2026, 8, 1),
                due_on=date(2026, 9, 15),
                amount_minor=13870,
                currency="AUD",
                status="unpaid",
            ),
            Bill(
                bill_id="BILL-3001",
                citizen_id="CITIZEN-3001",
                account_reference="WATER-5190",
                description="Quarterly water usage",
                issued_on=date(2026, 7, 1),
                due_on=date(2026, 8, 15),
                amount_minor=7540,
                currency="AUD",
                status="unpaid",
            ),
            Bill(
                bill_id="BILL-3002",
                citizen_id="CITIZEN-3001",
                account_reference="WATER-5190",
                description="Quarterly water usage",
                issued_on=date(2026, 4, 1),
                due_on=date(2026, 5, 15),
                amount_minor=6815,
                currency="AUD",
                status="paid",
                paid_at=datetime(2026, 5, 8, 16, 40, tzinfo=UTC),
            ),
        ]
        for bill in demo_bills:
            # 服务重启时不覆盖已有账单，特别是不覆盖已经付款后的状态。
            if session.get(Bill, bill.bill_id) is None:
                session.add(bill)
        session.flush()

        demo_payments = [
            (
                "BILL-1002",
                "PAY-1002-DEMO",
                "RCT-1002-DEMO",
                datetime(2026, 6, 12, 9, 30, tzinfo=UTC),
            ),
            (
                "BILL-1003",
                "PAY-1003-DEMO",
                "RCT-1003-DEMO",
                datetime(2026, 5, 9, 11, 20, tzinfo=UTC),
            ),
            (
                "BILL-2002",
                "PAY-2002-DEMO",
                "RCT-2002-DEMO",
                datetime(2026, 5, 10, 10, 15, tzinfo=UTC),
            ),
            (
                "BILL-2003",
                "PAY-2003-DEMO",
                "RCT-2003-DEMO",
                datetime(2026, 2, 11, 14, 5, tzinfo=UTC),
            ),
            (
                "BILL-3002",
                "PAY-3002-DEMO",
                "RCT-3002-DEMO",
                datetime(2026, 5, 8, 16, 40, tzinfo=UTC),
            ),
        ]
        # 已缴账单也补一条付款记录，这样回执页面可以直接打开演示。
        for bill_id, payment_id, receipt_number, paid_at in demo_payments:
            bill = session.get(Bill, bill_id)
            if bill is None:
                continue
            if bill.paid_at is None:
                bill.paid_at = paid_at
            if (
                session.query(Payment)
                .filter(Payment.bill_id == bill_id)
                .one_or_none()
                is None
            ):
                session.add(
                    Payment(
                        payment_id=payment_id,
                        bill_id=bill_id,
                        citizen_id=bill.citizen_id,
                        amount_minor=bill.amount_minor,
                        currency=bill.currency,
                        payment_method="card",
                        status="completed",
                        paid_at=paid_at,
                        receipt_number=receipt_number,
                    )
                )
        session.commit()


def reset_database_for_testing(database_url: str) -> None:
    # 测试每次都从干净的演示数据开始，避免上一条测试影响下一条。
    configure(database_url)
    Base.metadata.drop_all(bind=engine)
    initialise_database()


def get_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


configure()
