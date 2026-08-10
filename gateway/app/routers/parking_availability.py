from __future__ import annotations

import os
from typing import Any
from uuid import uuid4

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter(tags=["Parking Availability"])

SERVICE_URL = os.getenv(
    "PARKING_AVAILABILITY_SERVICE_URL", "http://localhost:8301"
).rstrip("/")
TIMEOUT_SECONDS = float(os.getenv("DOWNSTREAM_TIMEOUT_SECONDS", "5"))


def envelope(
    request_id: str,
    *,
    data: Any = None,
    message: str | None = None,
    error: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if error is not None:
        return {"success": False, "error": error, "meta": {"request_id": request_id}}
    return {
        "success": True,
        "data": data,
        "message": message,
        "meta": {"request_id": request_id},
    }


async def proxy(
    request: Request,
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
) -> JSONResponse:
    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            response = await client.request(
                method,
                f"{SERVICE_URL}{path}",
                params=request.query_params,
                json=payload,
                headers={"X-Request-ID": request_id},
            )
    except httpx.TimeoutException:
        return JSONResponse(
            status_code=504,
            content=envelope(
                request_id,
                error={
                    "code": "PARKING_AVAILABILITY_TIMEOUT",
                    "message": "The parking availability service timed out.",
                    "details": None,
                },
            ),
            headers={"X-Request-ID": request_id},
        )
    except httpx.HTTPError:
        return JSONResponse(
            status_code=503,
            content=envelope(
                request_id,
                error={
                    "code": "PARKING_AVAILABILITY_UNAVAILABLE",
                    "message": "The parking availability service is unavailable.",
                    "details": None,
                },
            ),
            headers={"X-Request-ID": request_id},
        )

    try:
        downstream = response.json()
    except ValueError:
        downstream = None
    if response.is_error:
        downstream_error = (
            downstream.get("error") if isinstance(downstream, dict) else None
        )
        error = downstream_error or {
            "code": "PARKING_AVAILABILITY_ERROR",
            "message": "The parking availability request failed.",
            "details": None,
        }
        return JSONResponse(
            status_code=response.status_code,
            content=envelope(request_id, error=error),
            headers={"X-Request-ID": request_id},
        )
    return JSONResponse(
        status_code=response.status_code,
        content=envelope(
            request_id,
            data=downstream,
            message="Parking availability request completed.",
        ),
        headers={"X-Request-ID": request_id},
    )


@router.get("/api/v1/parking-lots")
async def list_parking_lots(request: Request) -> JSONResponse:
    return await proxy(request, "GET", "/api/v1/parking-lots")


@router.get("/api/v1/parking-lots/{lot_id}")
async def get_parking_lot(lot_id: str, request: Request) -> JSONResponse:
    return await proxy(request, "GET", f"/api/v1/parking-lots/{lot_id}")


@router.patch("/api/v1/parking-lots/{lot_id}/availability")
async def update_parking_lot_availability(
    lot_id: str, payload: dict[str, Any], request: Request
) -> JSONResponse:
    return await proxy(
        request,
        "PATCH",
        f"/api/v1/parking-lots/{lot_id}/availability",
        payload,
    )
