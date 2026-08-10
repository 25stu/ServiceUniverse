from __future__ import annotations

import os
from typing import Any
from uuid import uuid4

import httpx
from fastapi import APIRouter, Request, Response, status

router = APIRouter(tags=["Attraction Reservation"])
ATTRACTION_SERVICE_URL = os.getenv(
    "ATTRACTION_SERVICE_URL", "http://localhost:8201"
).rstrip("/")
TIMEOUT_SECONDS = float(os.getenv("DOWNSTREAM_TIMEOUT_SECONDS", "5"))


def request_id_from(request: Request) -> str:
    return request.headers.get("X-Request-ID") or str(uuid4())


def success_envelope(
    data: Any,
    request_id: str,
    message: str = "Operation completed successfully.",
) -> dict[str, Any]:
    return {
        "success": True,
        "data": data,
        "message": message,
        "meta": {"request_id": request_id},
    }


def error_envelope(
    code: str,
    message: str,
    request_id: str,
    details: Any = None,
) -> dict[str, Any]:
    return {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "details": details,
        },
        "meta": {"request_id": request_id},
    }


async def forward(
    method: str,
    path: str,
    request: Request,
    response: Response,
    json_body: Any = None,
) -> dict[str, Any]:
    request_id = request_id_from(request)
    response.headers["X-Request-ID"] = request_id
    timeout = httpx.Timeout(TIMEOUT_SECONDS)

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            downstream = await client.request(
                method,
                f"{ATTRACTION_SERVICE_URL}{path}",
                params=request.query_params,
                json=json_body,
                headers={"X-Request-ID": request_id},
            )
    except httpx.TimeoutException:
        response.status_code = status.HTTP_504_GATEWAY_TIMEOUT
        return error_envelope(
            "DOWNSTREAM_TIMEOUT",
            "Attraction Reservation service timed out.",
            request_id,
        )
    except httpx.HTTPError:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return error_envelope(
            "DOWNSTREAM_UNAVAILABLE",
            "Attraction Reservation service is unavailable.",
            request_id,
        )

    if downstream.is_error:
        response.status_code = downstream.status_code
        try:
            payload = downstream.json()
        except ValueError:
            payload = {}
        detail = payload.get("detail", payload)
        if not isinstance(detail, dict):
            detail = {}
        return error_envelope(
            str(detail.get("code", "ATTRACTION_SERVICE_ERROR")),
            str(detail.get("message", "Attraction Reservation request failed.")),
            request_id,
            detail.get("details"),
        )

    response.status_code = downstream.status_code
    return success_envelope(
        downstream.json(),
        request_id,
        "Attraction Reservation request completed.",
    )


@router.get("/api/v1/attractions")
async def list_attractions(request: Request, response: Response) -> dict[str, Any]:
    return await forward("GET", "/api/v1/attractions", request, response)


@router.post("/api/v1/reservations")
async def create_reservation(
    request: Request, response: Response
) -> dict[str, Any]:
    return await forward(
        "POST",
        "/api/v1/reservations",
        request,
        response,
        await request.json(),
    )


@router.get("/api/v1/reservations/{reservation_id}")
async def get_reservation(
    reservation_id: str, request: Request, response: Response
) -> dict[str, Any]:
    return await forward(
        "GET",
        f"/api/v1/reservations/{reservation_id}",
        request,
        response,
    )


@router.patch("/api/v1/reservations/{reservation_id}/status")
async def update_reservation_status(
    reservation_id: str, request: Request, response: Response
) -> dict[str, Any]:
    return await forward(
        "PATCH",
        f"/api/v1/reservations/{reservation_id}/status",
        request,
        response,
        await request.json(),
    )
