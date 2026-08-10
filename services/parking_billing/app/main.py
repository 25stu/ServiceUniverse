from __future__ import annotations

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, Literal

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from services.parking_billing.app.repositories import BillingRepository
from services.parking_billing.app.schemas import (
    ParkingPaymentCreate,
    ParkingPaymentResponse,
    ParkingSessionCreate,
    ParkingSessionEnd,
    ParkingSessionResponse,
    ProcessEventResponse,
)


def error_payload(code: str, message: str, details: Any = None) -> dict[str, Any]:
    return {"error": {"code": code, "message": message, "details": details}}


ERRORS = {
    "PARKING_SESSION_NOT_FOUND": (404, "The requested parking session was not found."),
    "ACTIVE_SESSION_EXISTS": (
        409,
        "This vehicle already has an active parking session.",
    ),
    "SESSION_ALREADY_ENDED": (409, "This parking session has already ended."),
    "INVALID_END_TIME": (400, "The end time must be after the session start time."),
    "SESSION_NOT_BILLABLE": (409, "The parking session must end before payment."),
    "SESSION_ALREADY_PAID": (409, "This parking session has already been paid."),
}


def raise_business_error(code: str) -> None:
    status_code, message = ERRORS[code]
    raise HTTPException(status_code=status_code, detail=error_payload(code, message))


def create_app(database_url: str | None = None) -> FastAPI:
    repository = BillingRepository(
        database_url or os.getenv("PARKING_BILLING_DATABASE_URL")
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        repository.initialize()
        app.state.repository = repository
        yield

    application = FastAPI(
        title="Parking Billing and Payment Service",
        version="0.1.0",
        lifespan=lifespan,
    )

    @application.exception_handler(RequestValidationError)
    async def validation_error_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=error_payload(
                "VALIDATION_ERROR",
                "The request data is invalid.",
                jsonable_encoder(exc.errors()),
            ),
        )

    @application.get("/health")
    async def health() -> dict[str, str]:
        return {
            "status": "healthy",
            "service": "parking-billing",
            "version": "0.1.0",
        }

    @application.get("/api/v1/service-info")
    async def service_info() -> dict[str, str]:
        return {
            "service": "parking-billing",
            "owner": "E",
            "implementation": "business_service",
            "status": "implemented",
        }

    @application.post(
        "/api/v1/parking-sessions",
        response_model=ParkingSessionResponse,
        status_code=201,
    )
    async def create_parking_session(
        payload: ParkingSessionCreate, request: Request
    ) -> ParkingSessionResponse:
        parking_session, error = request.app.state.repository.create_session(
            payload.citizen_id,
            payload.vehicle_plate,
            payload.parking_lot_id,
            payload.started_at,
        )
        if error:
            raise_business_error(error)
        assert parking_session is not None
        return ParkingSessionResponse.model_validate(parking_session)

    @application.get(
        "/api/v1/parking-sessions", response_model=list[ParkingSessionResponse]
    )
    async def list_parking_sessions(
        request: Request,
        citizen_id: str | None = None,
        status: Literal["active", "completed"] | None = Query(default=None),
    ) -> list[ParkingSessionResponse]:
        sessions = request.app.state.repository.list_sessions(citizen_id, status)
        return [ParkingSessionResponse.model_validate(item) for item in sessions]

    @application.get(
        "/api/v1/parking-sessions/{session_id}",
        response_model=ParkingSessionResponse,
    )
    async def get_parking_session(
        session_id: str, request: Request
    ) -> ParkingSessionResponse:
        parking_session = request.app.state.repository.get_session(session_id)
        if parking_session is None:
            raise_business_error("PARKING_SESSION_NOT_FOUND")
        return ParkingSessionResponse.model_validate(parking_session)

    @application.post(
        "/api/v1/parking-sessions/{session_id}/end",
        response_model=ParkingSessionResponse,
    )
    async def end_parking_session(
        session_id: str, payload: ParkingSessionEnd, request: Request
    ) -> ParkingSessionResponse:
        parking_session, error = request.app.state.repository.end_session(
            session_id, payload.ended_at
        )
        if error:
            raise_business_error(error)
        assert parking_session is not None
        return ParkingSessionResponse.model_validate(parking_session)

    @application.post(
        "/api/v1/parking-payments",
        response_model=ParkingPaymentResponse,
        status_code=201,
    )
    async def create_parking_payment(
        payload: ParkingPaymentCreate, request: Request
    ) -> ParkingPaymentResponse:
        payment, error = request.app.state.repository.create_payment(
            payload.session_id, payload.payment_method
        )
        if error:
            raise_business_error(error)
        assert payment is not None
        return ParkingPaymentResponse.model_validate(payment)

    @application.get(
        "/api/v1/parking-payments/{payment_id}",
        response_model=ParkingPaymentResponse,
    )
    async def get_parking_payment(
        payment_id: str, request: Request
    ) -> ParkingPaymentResponse:
        payment = request.app.state.repository.get_payment(payment_id)
        if payment is None:
            raise HTTPException(
                status_code=404,
                detail=error_payload(
                    "PARKING_PAYMENT_NOT_FOUND",
                    "The requested parking payment was not found.",
                ),
            )
        return ParkingPaymentResponse.model_validate(payment)

    @application.get(
        "/api/v1/parking-sessions/{session_id}/events",
        response_model=list[ProcessEventResponse],
    )
    async def list_parking_session_events(
        session_id: str, request: Request
    ) -> list[ProcessEventResponse]:
        events = request.app.state.repository.list_events(session_id)
        if events is None:
            raise_business_error("PARKING_SESSION_NOT_FOUND")
        return [ProcessEventResponse.model_validate(item) for item in events]

    @application.exception_handler(HTTPException)
    async def http_error_handler(_request: Request, exc: HTTPException) -> JSONResponse:
        content = exc.detail
        if not isinstance(content, dict) or "error" not in content:
            content = error_payload("HTTP_ERROR", str(exc.detail))
        return JSONResponse(status_code=exc.status_code, content=content)

    return application


app = create_app()
