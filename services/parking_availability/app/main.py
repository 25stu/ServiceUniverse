from __future__ import annotations

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from services.parking_availability.app.repositories import ParkingLotRepository
from services.parking_availability.app.schemas import (
    AvailabilityUpdate,
    ParkingLotResponse,
)


def error_payload(code: str, message: str, details: Any = None) -> dict[str, Any]:
    return {"error": {"code": code, "message": message, "details": details}}


def create_app(database_url: str | None = None) -> FastAPI:
    repository = ParkingLotRepository(
        database_url or os.getenv("PARKING_AVAILABILITY_DATABASE_URL")
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        repository.initialize()
        app.state.repository = repository
        yield

    application = FastAPI(
        title="Public Parking Availability Service",
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
            "service": "parking-availability",
            "version": "0.1.0",
        }

    @application.get("/api/v1/service-info")
    async def service_info() -> dict[str, str]:
        return {
            "service": "parking-availability",
            "owner": "E",
            "implementation": "selected_microservice",
            "status": "implemented",
        }

    @application.get(
        "/api/v1/parking-lots", response_model=list[ParkingLotResponse]
    )
    async def list_parking_lots(request: Request) -> list[ParkingLotResponse]:
        items = request.app.state.repository.list_parking_lots()
        return [ParkingLotResponse.model_validate(item) for item in items]

    @application.get(
        "/api/v1/parking-lots/{lot_id}", response_model=ParkingLotResponse
    )
    async def get_parking_lot(lot_id: str, request: Request) -> ParkingLotResponse:
        parking_lot = request.app.state.repository.get_parking_lot(lot_id)
        if parking_lot is None:
            raise HTTPException(
                status_code=404,
                detail=error_payload(
                    "PARKING_LOT_NOT_FOUND",
                    "The requested parking lot was not found.",
                ),
            )
        return ParkingLotResponse.model_validate(parking_lot)

    @application.patch(
        "/api/v1/parking-lots/{lot_id}/availability",
        response_model=ParkingLotResponse,
    )
    async def update_availability(
        lot_id: str, payload: AvailabilityUpdate, request: Request
    ) -> ParkingLotResponse:
        parking_lot, updated = request.app.state.repository.update_availability(
            lot_id, payload.available_spaces
        )
        if parking_lot is None:
            raise HTTPException(
                status_code=404,
                detail=error_payload(
                    "PARKING_LOT_NOT_FOUND",
                    "The requested parking lot was not found.",
                ),
            )
        if not updated:
            raise HTTPException(
                status_code=409,
                detail=error_payload(
                    "AVAILABILITY_EXCEEDS_CAPACITY",
                    "Available spaces cannot exceed the parking lot capacity.",
                    {
                        "total_spaces": parking_lot.total_spaces,
                        "available_spaces": payload.available_spaces,
                    },
                ),
            )
        return ParkingLotResponse.model_validate(parking_lot)

    @application.exception_handler(HTTPException)
    async def http_error_handler(_request: Request, exc: HTTPException) -> JSONResponse:
        content = exc.detail
        if not isinstance(content, dict) or "error" not in content:
            content = error_payload("HTTP_ERROR", str(exc.detail))
        return JSONResponse(status_code=exc.status_code, content=content)

    return application


app = create_app()
