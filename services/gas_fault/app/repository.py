from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from services.gas_fault.app.models import (
    FaultReportRecord,
    FaultStatusHistoryRecord,
)


class FaultReportRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self.session_factory = session_factory

    def create(
        self,
        report: FaultReportRecord,
        initial_event: FaultStatusHistoryRecord,
    ) -> FaultReportRecord:
        with self.session_factory() as session:
            session.add_all([report, initial_event])
            session.commit()
            return report

    def get(self, report_id: str) -> FaultReportRecord | None:
        with self.session_factory() as session:
            return session.get(FaultReportRecord, report_id)

    def list_reports(
        self, citizen_id: str | None = None
    ) -> list[FaultReportRecord]:
        with self.session_factory() as session:
            statement = select(FaultReportRecord)
            if citizen_id is not None:
                statement = statement.where(
                    FaultReportRecord.citizen_id == citizen_id
                )
            statement = statement.order_by(FaultReportRecord.created_at.desc())
            return list(session.scalars(statement))

    def history(self, report_id: str) -> list[FaultStatusHistoryRecord]:
        with self.session_factory() as session:
            statement = (
                select(FaultStatusHistoryRecord)
                .where(FaultStatusHistoryRecord.report_id == report_id)
                .order_by(FaultStatusHistoryRecord.event_id)
            )
            return list(session.scalars(statement))

    def update_status(
        self,
        report_id: str,
        status: str,
        updated_at: str,
        event: FaultStatusHistoryRecord,
    ) -> FaultReportRecord | None:
        with self.session_factory() as session:
            report = session.get(FaultReportRecord, report_id)
            if report is None:
                return None
            report.status = status
            report.updated_at = updated_at
            session.add(event)
            session.commit()
            return report
