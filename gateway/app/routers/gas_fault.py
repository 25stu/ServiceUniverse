from __future__ import annotations

import os
from uuid import uuid4

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/v1", tags=["Gas Fault"])

GAS_SERVICE_URL = os.getenv("GAS_SERVICE_URL", "http://localhost:8102").rstrip("/")
TIMEOUT_SECONDS = float(os.getenv("DOWNSTREAM_TIMEOUT_SECONDS", "5"))


def error_response(
    status_code: int,
    request_id: str,
    code: str,
    message: str,
    details: object | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {"code": code, "message": message, "details": details},
            "meta": {"request_id": request_id},
        },
        headers={"X-Request-ID": request_id},
    )


async def proxy_request(
    request: Request,
    method: str,
    path: str,
    success_message: str,
) -> JSONResponse:
    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    headers = {"X-Request-ID": request_id, "Accept": "application/json"}
    if citizen_id := request.headers.get("X-Citizen-ID"):
        headers["X-Citizen-ID"] = citizen_id
    if user_role := request.headers.get("X-User-Role"):
        headers["X-User-Role"] = user_role
    body = await request.body()
    if body:
        headers["Content-Type"] = "application/json"

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            response = await client.request(
                method,
                f"{GAS_SERVICE_URL}{path}",
                headers=headers,
                content=body or None,
            )
    except httpx.TimeoutException:
        return error_response(
            504,
            request_id,
            "GAS_SERVICE_TIMEOUT",
            "The gas fault service did not respond in time.",
        )
    except httpx.RequestError:
        return error_response(
            503,
            request_id,
            "GAS_SERVICE_UNAVAILABLE",
            "The gas fault service is currently unavailable.",
        )

    try:
        payload = response.json()
    except ValueError:
        return error_response(
            502,
            request_id,
            "INVALID_DOWNSTREAM_RESPONSE",
            "The gas fault service returned an invalid response.",
        )

    if response.is_error:
        downstream_error = payload.get("error", {})
        return error_response(
            response.status_code,
            request_id,
            downstream_error.get("code", "GAS_SERVICE_ERROR"),
            downstream_error.get(
                "message", "The gas fault request could not be completed."
            ),
            downstream_error.get("details"),
        )

    return JSONResponse(
        status_code=response.status_code,
        content={
            "success": True,
            "data": payload,
            "message": success_message,
            "meta": {"request_id": request_id},
        },
        headers={"X-Request-ID": request_id},
    )


@router.post("/fault-reports")
async def create_fault_report(request: Request) -> JSONResponse:
    return await proxy_request(
        request,
        "POST",
        "/api/v1/fault-reports",
        "Fault report created successfully.",
    )


@router.get("/fault-reports")
async def list_fault_reports(request: Request) -> JSONResponse:
    return await proxy_request(
        request,
        "GET",
        "/api/v1/fault-reports",
        "Fault reports retrieved successfully.",
    )


@router.get("/fault-reports/{report_id}")
async def get_fault_report(report_id: str, request: Request) -> JSONResponse:
    return await proxy_request(
        request,
        "GET",
        f"/api/v1/fault-reports/{report_id}",
        "Fault report retrieved successfully.",
    )


@router.patch("/fault-reports/{report_id}/status")
async def update_fault_status(report_id: str, request: Request) -> JSONResponse:
    return await proxy_request(
        request,
        "PATCH",
        f"/api/v1/fault-reports/{report_id}/status",
        "Repair status updated successfully.",
    )


@router.post("/fault-reports/{report_id}/cancel")
async def cancel_fault_report(report_id: str, request: Request) -> JSONResponse:
    return await proxy_request(
        request,
        "POST",
        f"/api/v1/fault-reports/{report_id}/cancel",
        "Fault report cancelled successfully.",
    )
