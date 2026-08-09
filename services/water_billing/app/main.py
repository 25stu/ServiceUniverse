from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from services.water_billing.app.api import router
from services.water_billing.app.database import initialise_database
from services.water_billing.app.services.billing import WaterBillingError


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    initialise_database()
    yield


app = FastAPI(
    title="Water Billing and Payment Service",
    version="0.1.0",
    lifespan=lifespan,
)
app.include_router(router)


@app.exception_handler(WaterBillingError)
async def handle_water_billing_error(
    _request: Request, error: WaterBillingError
) -> JSONResponse:
    return JSONResponse(
        status_code=error.status_code,
        content={"code": error.code, "message": error.message},
    )


@app.exception_handler(RequestValidationError)
async def handle_validation_error(
    _request: Request, error: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "code": "VALIDATION_ERROR",
            "message": "The request did not satisfy the required format.",
            "details": error.errors(),
        },
    )


@app.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "healthy",
        "service": "water-billing",
        "version": "0.1.0",
    }


@app.get("/api/v1/service-info")
async def service_info() -> dict[str, str]:
    return {
        "service": "water-billing",
        "owner": "A",
        "implementation": "selected_microservice",
        "status": "available",
    }
