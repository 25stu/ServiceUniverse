from __future__ import annotations

import os
from typing import Any
from urllib.parse import urlencode
from uuid import uuid4

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response

router = APIRouter(tags=["Water Billing"])

WATER_SERVICE_URL = os.getenv("WATER_SERVICE_URL", "http://localhost:8101")
TIMEOUT_SECONDS = float(os.getenv("DOWNSTREAM_TIMEOUT_SECONDS", "5"))


def error_response(
    status_code: int, code: str, message: str, request_id: str, details: Any = None
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


def success_response(
    status_code: int, data: Any, message: str, request_id: str
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "success": True,
            "data": data,
            "message": message,
            "meta": {"request_id": request_id},
        },
        headers={"X-Request-ID": request_id},
    )


async def request_water_service(
    method: str, path: str, request_id: str, payload: dict[str, Any] | None = None
) -> httpx.Response:
    timeout = httpx.Timeout(TIMEOUT_SECONDS)
    async with httpx.AsyncClient(timeout=timeout) as client:
        return await client.request(
            method,
            f"{WATER_SERVICE_URL.rstrip('/')}{path}",
            headers={"X-Request-ID": request_id},
            json=payload,
        )


async def request_water_pdf(
    path: str, request_id: str
) -> tuple[int, bytes, str | None, dict[str, Any] | None]:
    # 下载 PDF 不能按普通 JSON 接口处理，所以这里单独保留文件内容和文件名。
    timeout = httpx.Timeout(TIMEOUT_SECONDS)
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.get(
            f"{WATER_SERVICE_URL.rstrip('/')}{path}",
            headers={"X-Request-ID": request_id},
        )
    if response.is_error:
        try:
            return response.status_code, b"", None, response.json()
        except ValueError:
            return response.status_code, b"", None, None
    return (
        response.status_code,
        response.content,
        response.headers.get("content-disposition"),
        None,
    )


async def forward_water_request(
    method: str,
    path: str,
    request: Request,
    payload: dict[str, Any] | None = None,
    success_message: str = "Operation completed successfully.",
) -> JSONResponse:
    # 网关给同一次请求带上 request_id，前端看到的成功和失败格式也保持一致。
    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    try:
        response = await request_water_service(method, path, request_id, payload)
    except httpx.TimeoutException:
        return error_response(
            504,
            "DOWNSTREAM_TIMEOUT",
            "The Water Billing service did not respond in time.",
            request_id,
        )
    except httpx.HTTPError:
        return error_response(
            503,
            "WATER_SERVICE_UNAVAILABLE",
            "The Water Billing service is currently unavailable.",
            request_id,
        )

    try:
        response_payload = response.json()
    except ValueError:
        return error_response(
            502,
            "INVALID_DOWNSTREAM_RESPONSE",
            "The Water Billing service returned an invalid response.",
            request_id,
        )

    if response.is_error:
        return error_response(
            response.status_code,
            response_payload.get("code", "WATER_SERVICE_ERROR"),
            response_payload.get("message", "The Water Billing request failed."),
            request_id,
            response_payload.get("details"),
        )
    return success_response(
        response.status_code,
        response_payload,
        success_message,
        request_id,
    )


@router.get("/api/v1/bills")
async def list_bills(request: Request, citizen_id: str) -> JSONResponse:
    return await forward_water_request(
        "GET",
        f"/api/v1/bills?{urlencode({'citizen_id': citizen_id})}",
        request,
        success_message="Bills retrieved successfully.",
    )


@router.get("/api/v1/bills/{bill_id}")
async def get_bill(bill_id: str, request: Request) -> JSONResponse:
    return await forward_water_request(
        "GET",
        f"/api/v1/bills/{bill_id}",
        request,
        success_message="Bill retrieved successfully.",
    )


@router.get("/api/v1/bills/{bill_id}/receipt")
async def get_bill_receipt(bill_id: str, request: Request) -> JSONResponse:
    return await forward_water_request(
        "GET",
        f"/api/v1/bills/{bill_id}/receipt",
        request,
        success_message="Payment receipt retrieved successfully.",
    )


@router.get("/api/v1/bills/{bill_id}/receipt.pdf")
async def download_bill_receipt(bill_id: str, request: Request) -> Response:
    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    try:
        status_code, content, disposition, error_payload = await request_water_pdf(
            f"/api/v1/bills/{bill_id}/receipt.pdf", request_id
        )
    except httpx.TimeoutException:
        return error_response(
            504,
            "DOWNSTREAM_TIMEOUT",
            "The Water Billing service did not respond in time.",
            request_id,
        )
    except httpx.HTTPError:
        return error_response(
            503,
            "WATER_SERVICE_UNAVAILABLE",
            "The Water Billing service is currently unavailable.",
            request_id,
        )

    if error_payload is not None:
        return error_response(
            status_code,
            error_payload.get("code", "WATER_SERVICE_ERROR"),
            error_payload.get("message", "The Water Billing request failed."),
            request_id,
            error_payload.get("details"),
        )
    # 文件下载时把下游服务给的附件文件名继续带给浏览器。
    headers = {"X-Request-ID": request_id}
    if disposition is not None:
        headers["Content-Disposition"] = disposition
    return Response(content=content, media_type="application/pdf", headers=headers)


@router.post("/api/v1/payments")
async def create_payment(request: Request, payload: dict[str, Any]) -> JSONResponse:
    return await forward_water_request(
        "POST",
        "/api/v1/payments",
        request,
        payload,
        "Payment completed successfully.",
    )


@router.get("/api/v1/payments/{payment_id}")
async def get_payment(payment_id: str, request: Request) -> JSONResponse:
    return await forward_water_request(
        "GET",
        f"/api/v1/payments/{payment_id}",
        request,
        success_message="Payment receipt retrieved successfully.",
    )
