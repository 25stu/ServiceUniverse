from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from services.gas_fault.app.models import (
    FaultReportRecord,
    FaultStatusHistoryRecord,
)
from services.gas_fault.app.repository import FaultReportRepository
from services.gas_fault.app.schemas import (
    FaultReport,
    FaultReportCreate,
    FaultStatus,
    FaultStatusHistory,
    FaultStatusUpdate,
)

ACTIVITY_BY_STATUS = {
    FaultStatus.REPORTED: "Submit Fault Report",
    FaultStatus.ASSIGNED: "Assign Repair Team",
    FaultStatus.INSPECTION_IN_PROGRESS: "Inspect Fault",
    FaultStatus.REPAIR_IN_PROGRESS: "Repair Fault",
    FaultStatus.RESOLVED: "Resolve Fault",
    FaultStatus.CLOSED: "Close Fault Report",
    FaultStatus.CANCELLED: "Cancel Fault Report",
}

ALLOWED_TRANSITIONS = {
    FaultStatus.REPORTED: {FaultStatus.ASSIGNED, FaultStatus.CANCELLED},
    FaultStatus.ASSIGNED: {
        FaultStatus.INSPECTION_IN_PROGRESS,
        FaultStatus.CANCELLED,
    },
    FaultStatus.INSPECTION_IN_PROGRESS: {
        FaultStatus.REPAIR_IN_PROGRESS,
        FaultStatus.CANCELLED,
    },
    FaultStatus.REPAIR_IN_PROGRESS: {
        FaultStatus.RESOLVED,
        FaultStatus.CANCELLED,
    },
    FaultStatus.RESOLVED: {FaultStatus.CLOSED, FaultStatus.REPAIR_IN_PROGRESS},
    FaultStatus.CLOSED: set(),
    FaultStatus.CANCELLED: set(),
}


class GasFaultError(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: object | None = None,
    ) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details
        super().__init__(message)


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


class GasFaultService:
    def __init__(self, repository: FaultReportRepository) -> None:
        self.repository = repository

    def create_report(self, payload: FaultReportCreate) -> FaultReport:
        report_id = f"FAULT-{uuid4().hex[:8].upper()}"
        timestamp = utc_now()
        report = FaultReportRecord(
            report_id=report_id,
            citizen_id=payload.citizen_id,
            reporter_name=payload.reporter_name,
            contact_phone=payload.contact_phone,
            address=payload.address,
            description=payload.description,
            severity=payload.severity.value,
            status=FaultStatus.REPORTED.value,
            created_at=timestamp,
            updated_at=timestamp,
        )
        event = FaultStatusHistoryRecord(
            report_id=report_id,
            status=FaultStatus.REPORTED.value,
            activity=ACTIVITY_BY_STATUS[FaultStatus.REPORTED],
            resource="Citizen",
            note="Fault report submitted.",
            timestamp=timestamp,
        )
        self.repository.create(report, event)
        return self._response(report)

    def get_report(self, report_id: str) -> FaultReport:
        report = self.repository.get(report_id.upper())
        if report is None:
            raise GasFaultError(
                404,
                "FAULT_REPORT_NOT_FOUND",
                "The requested fault report was not found.",
            )
        return self._response(report)

    def list_reports(self, citizen_id: str | None = None) -> list[FaultReport]:
        return [
            self._response(report)
            for report in self.repository.list_reports(citizen_id=citizen_id)
        ]

    def update_status(
        self, report_id: str, payload: FaultStatusUpdate
    ) -> FaultReport:
        normalized_id = report_id.upper()
        report = self.repository.get(normalized_id)
        if report is None:
            raise GasFaultError(
                404,
                "FAULT_REPORT_NOT_FOUND",
                "The requested fault report was not found.",
            )

        current = FaultStatus(report.status)
        if payload.status not in ALLOWED_TRANSITIONS[current]:
            raise GasFaultError(
                409,
                "INVALID_FAULT_STATUS_TRANSITION",
                f"The fault report cannot move from {current.value} "
                f"to {payload.status.value}.",
                {
                    "current_status": current.value,
                    "requested_status": payload.status.value,
                    "allowed_statuses": sorted(
                        status.value for status in ALLOWED_TRANSITIONS[current]
                    ),
                },
            )

        timestamp = utc_now()
        event = FaultStatusHistoryRecord(
            report_id=normalized_id,
            status=payload.status.value,
            activity=ACTIVITY_BY_STATUS[payload.status],
            resource=payload.resource,
            note=payload.note,
            timestamp=timestamp,
        )
        updated = self.repository.update_status(
            normalized_id,
            payload.status.value,
            timestamp,
            event,
        )
        if updated is None:
            raise GasFaultError(
                404,
                "FAULT_REPORT_NOT_FOUND",
                "The requested fault report was not found.",
            )
        return self._response(updated)

    def cancel_report(self, report_id: str) -> FaultReport:
        return self.update_status(
            report_id,
            FaultStatusUpdate(
                status=FaultStatus.CANCELLED,
                resource="Citizen",
                note="The citizen cancelled this fault report.",
            ),
        )

    def _response(self, report: FaultReportRecord) -> FaultReport:
        history = [
            FaultStatusHistory(
                status=event.status,
                activity=event.activity,
                resource=event.resource,
                note=event.note,
                timestamp=event.timestamp,
            )
            for event in self.repository.history(report.report_id)
        ]
        return FaultReport(
            report_id=report.report_id,
            citizen_id=report.citizen_id,
            reporter_name=report.reporter_name,
            contact_phone=report.contact_phone,
            address=report.address,
            description=report.description,
            severity=report.severity,
            status=report.status,
            created_at=report.created_at,
            updated_at=report.updated_at,
            history=history,
        )
