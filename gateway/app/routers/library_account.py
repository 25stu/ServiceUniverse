from __future__ import annotations

import os
from typing import Any
from uuid import uuid4

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter(tags=["Library Account"])


async def request_library_service(
    method: str,
    path: str,
    payload: dict[str, Any] | None,
    request_id: str,
) -> tuple[int, dict[str, Any]]:
    base_url = os.getenv("LIBRARY_SERVICE_URL", "http://localhost:8202").rstrip("/")
    timeout = float(os.getenv("DOWNSTREAM_TIMEOUT_SECONDS", "5"))
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.request(
            method,
            f"{base_url}{path}",
            json=payload,
            headers={"X-Request-ID": request_id, "Accept": "application/json"},
        )
    try:
        response_payload = response.json()
    except ValueError:
        return 502, {
            "error": {
                "code": "INVALID_DOWNSTREAM_RESPONSE",
                "message": "The library service returned an invalid response.",
                "details": None,
            }
        }
    if response.status_code >= 500:
        mapped_status = (
            response.status_code if response.status_code in {503, 504} else 502
        )
        return mapped_status, {
            "error": {
                "code": "LIBRARY_SERVICE_UPSTREAM_ERROR",
                "message": "The library service could not complete the request.",
                "details": None,
            }
        }
    return response.status_code, response_payload


def envelope(
    status_code: int,
    payload: dict[str, Any],
    request_id: str,
    success_message: str,
) -> JSONResponse:
    if status_code >= 500 and status_code not in {502, 503, 504}:
        status_code = 502
        payload = {
            "error": {
                "code": "LIBRARY_SERVICE_UPSTREAM_ERROR",
                "message": "The library service could not complete the request.",
                "details": None,
            }
        }
    if 200 <= status_code < 300:
        content: dict[str, Any] = {
            "success": True,
            "data": payload,
            "message": success_message,
            "meta": {"request_id": request_id},
        }
    else:
        downstream_error = payload.get("error", {})
        content = {
            "success": False,
            "error": {
                "code": downstream_error.get("code", "LIBRARY_SERVICE_ERROR"),
                "message": downstream_error.get(
                    "message", "The library service could not complete the request."
                ),
                "details": downstream_error.get("details"),
            },
            "meta": {"request_id": request_id},
        }
    return JSONResponse(
        status_code=status_code,
        content=content,
        headers={"X-Request-ID": request_id},
    )


async def proxy_library_request(
    request: Request,
    method: str,
    path: str,
    success_message: str,
    payload: dict[str, Any] | None = None,
) -> JSONResponse:
    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    try:
        status_code, response_payload = await request_library_service(
            method, path, payload, request_id
        )
    except httpx.TimeoutException:
        status_code = 504
        response_payload = {
            "error": {
                "code": "LIBRARY_SERVICE_TIMEOUT",
                "message": "The library service did not respond in time.",
                "details": None,
            }
        }
    except httpx.RequestError:
        status_code = 503
        response_payload = {
            "error": {
                "code": "LIBRARY_SERVICE_UNAVAILABLE",
                "message": "The library service is currently unavailable.",
                "details": None,
            }
        }
    return envelope(status_code, response_payload, request_id, success_message)


@router.post("/api/v1/library-memberships")
async def create_library_membership(
    request: Request, application: dict[str, Any]
) -> JSONResponse:
    return await proxy_library_request(
        request,
        "POST",
        "/api/v1/library-memberships",
        "Library membership created successfully.",
        application,
    )


@router.get("/api/v1/library-accounts/{account_id}")
async def get_library_account(request: Request, account_id: str) -> JSONResponse:
    return await proxy_library_request(
        request,
        "GET",
        f"/api/v1/library-accounts/{account_id}",
        "Library account retrieved successfully.",
    )


@router.patch("/api/v1/library-accounts/{account_id}")
async def update_library_account(
    request: Request,
    account_id: str,
    update: dict[str, Any],
) -> JSONResponse:
    return await proxy_library_request(
        request,
        "PATCH",
        f"/api/v1/library-accounts/{account_id}",
        "Library account updated successfully.",
        update,
    )
