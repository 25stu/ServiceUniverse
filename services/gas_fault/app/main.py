from __future__ import annotations

from fastapi import FastAPI, Header, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from services.gas_fault.app.database import create_database
from services.gas_fault.app.repository import FaultReportRepository
from services.gas_fault.app.schemas import (
    FaultReport,
    FaultReportCreate,
    FaultStatusUpdate,
)
from services.gas_fault.app.service import GasFaultError, GasFaultService

ADMIN_ROLES = {"gas_admin", "gas_operator"}


def require_citizen_identity(citizen_id: str | None) -> str:
    if not citizen_id:
        raise GasFaultError(
            401,
            "ACTOR_IDENTITY_REQUIRED",
            "A citizen identity is required for this request.",
        )
    return citizen_id


def require_administrator(user_role: str | None) -> None:
    if not user_role:
        raise GasFaultError(
            401,
            "ACTOR_IDENTITY_REQUIRED",
            "An administrator identity is required for this request.",
        )
    if user_role not in ADMIN_ROLES:
        raise GasFaultError(
            403,
            "ADMINISTRATOR_ACCESS_REQUIRED",
            "Only an authorised gas operator can update repair status.",
        )


def create_app(database_url: str | None = None) -> FastAPI:
    application = FastAPI(
        title="Gas Fault Reporting and Repair Tracking Service",
        version="0.1.0",
    )
    _engine, session_factory = create_database(database_url)
    service = GasFaultService(FaultReportRepository(session_factory))

    @application.exception_handler(GasFaultError)
    async def gas_fault_error_handler(
        _request: Request, error: GasFaultError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=error.status_code,
            content={
                "error": {
                    "code": error.code,
                    "message": error.message,
                    "details": error.details,
                }
            },
        )

    @application.exception_handler(RequestValidationError)
    async def validation_error_handler(
        _request: Request, error: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "The request contains invalid data.",
                    "details": jsonable_encoder(error.errors()),
                }
            },
        )

    @application.get("/health")
    async def health() -> dict[str, str]:
        return {
            "status": "healthy",
            "service": "gas-fault",
            "version": "0.1.0",
        }

    @application.get("/api/v1/service-info")
    async def service_info() -> dict[str, str]:
        return {
            "service": "gas-fault",
            "owner": "B",
            "implementation": "business_service",
            "status": "operational",
        }

    @application.post(
        "/api/v1/fault-reports",
        response_model=FaultReport,
        status_code=status.HTTP_201_CREATED,
    )
    async def create_fault_report(
        payload: FaultReportCreate,
        x_citizen_id: str | None = Header(default=None),
    ) -> FaultReport:
        citizen_id = require_citizen_identity(x_citizen_id)
        if citizen_id != payload.citizen_id:
            raise GasFaultError(
                403,
                "CITIZEN_IDENTITY_MISMATCH",
                "A citizen can only submit a report for their own account.",
            )
        return service.create_report(payload)

    @application.get(
        "/api/v1/fault-reports",
        response_model=list[FaultReport],
    )
    async def list_fault_reports(
        x_user_role: str | None = Header(default=None),
        x_citizen_id: str | None = Header(default=None),
    ) -> list[FaultReport]:
        if x_user_role in ADMIN_ROLES:
            return service.list_reports()
        citizen_id = require_citizen_identity(x_citizen_id)
        return service.list_reports(citizen_id=citizen_id)

    @application.get(
        "/api/v1/fault-reports/{report_id}",
        response_model=FaultReport,
    )
    async def get_fault_report(
        report_id: str,
        x_user_role: str | None = Header(default=None),
        x_citizen_id: str | None = Header(default=None),
    ) -> FaultReport:
        report = service.get_report(report_id)
        if x_user_role in ADMIN_ROLES:
            return report
        citizen_id = require_citizen_identity(x_citizen_id)
        if report.citizen_id != citizen_id:
            raise GasFaultError(
                403,
                "FAULT_REPORT_ACCESS_DENIED",
                "A citizen can only view their own fault reports.",
            )
        return report

    @application.patch(
        "/api/v1/fault-reports/{report_id}/status",
        response_model=FaultReport,
    )
    async def update_fault_status(
        report_id: str,
        payload: FaultStatusUpdate,
        x_user_role: str | None = Header(default=None),
    ) -> FaultReport:
        require_administrator(x_user_role)
        return service.update_status(report_id, payload)

    @application.post(
        "/api/v1/fault-reports/{report_id}/cancel",
        response_model=FaultReport,
    )
    async def cancel_fault_report(
        report_id: str,
        x_citizen_id: str | None = Header(default=None),
    ) -> FaultReport:
        citizen_id = require_citizen_identity(x_citizen_id)
        report = service.get_report(report_id)
        if report.citizen_id != citizen_id:
            raise GasFaultError(
                403,
                "FAULT_REPORT_ACCESS_DENIED",
                "A citizen can only cancel their own fault reports.",
            )
        try:
            return service.cancel_report(report_id)
        except GasFaultError as error:
            if error.code == "INVALID_FAULT_STATUS_TRANSITION":
                raise GasFaultError(
                    409,
                    "FAULT_REPORT_CANNOT_BE_CANCELLED",
                    "This fault report can no longer be cancelled.",
                    {"current_status": report.status.value},
                ) from error
            raise

    return application


app = create_app()
