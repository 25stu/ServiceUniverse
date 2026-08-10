from __future__ import annotations

import os
from typing import Any
from uuid import uuid4

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter(tags=["Parking Billing"])

SERVICE_URL = os.getenv("PARKING_BILLING_SERVICE_URL", "http://localhost:8302").rstrip(
    "/"
)
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
                    "code": "PARKING_BILLING_TIMEOUT",
                    "message": "The parking billing service timed out.",
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
                    "code": "PARKING_BILLING_UNAVAILABLE",
                    "message": "The parking billing service is unavailable.",
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
            "code": "PARKING_BILLING_ERROR",
            "message": "The parking billing request failed.",
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
            message="Parking billing request completed.",
        ),
        headers={"X-Request-ID": request_id},
    )


@router.post("/api/v1/parking-sessions")
async def create_parking_session(
    payload: dict[str, Any], request: Request
) -> JSONResponse:
    return await proxy(request, "POST", "/api/v1/parking-sessions", payload)


@router.get("/api/v1/parking-sessions")
async def list_parking_sessions(request: Request) -> JSONResponse:
    return await proxy(request, "GET", "/api/v1/parking-sessions")


@router.get("/api/v1/parking-sessions/{session_id}")
async def get_parking_session(session_id: str, request: Request) -> JSONResponse:
    return await proxy(request, "GET", f"/api/v1/parking-sessions/{session_id}")


@router.post("/api/v1/parking-sessions/{session_id}/end")
async def end_parking_session(
    session_id: str, payload: dict[str, Any], request: Request
) -> JSONResponse:
    return await proxy(
        request, "POST", f"/api/v1/parking-sessions/{session_id}/end", payload
    )


@router.get("/api/v1/parking-sessions/{session_id}/events")
async def list_parking_session_events(
    session_id: str, request: Request
) -> JSONResponse:
    return await proxy(
        request, "GET", f"/api/v1/parking-sessions/{session_id}/events"
    )


@router.post("/api/v1/parking-payments")
async def create_parking_payment(
    payload: dict[str, Any], request: Request
) -> JSONResponse:
    return await proxy(request, "POST", "/api/v1/parking-payments", payload)


@router.get("/api/v1/parking-payments/{payment_id}")
async def get_parking_payment(payment_id: str, request: Request) -> JSONResponse:
    return await proxy(request, "GET", f"/api/v1/parking-payments/{payment_id}")
