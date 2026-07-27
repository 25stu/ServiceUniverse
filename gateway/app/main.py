from __future__ import annotations

import asyncio
import os
from uuid import uuid4

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from gateway.app.routers import (
    attraction_reservation,
    gas_fault,
    library_account,
    parking_availability,
    parking_billing,
    water_billing,
)

SERVICE_URLS = {
    "water-billing": os.getenv("WATER_SERVICE_URL", "http://localhost:8101"),
    "gas-fault": os.getenv("GAS_SERVICE_URL", "http://localhost:8102"),
    "attraction-reservation": os.getenv(
        "ATTRACTION_SERVICE_URL", "http://localhost:8201"
    ),
    "library-account": os.getenv(
        "LIBRARY_SERVICE_URL", "http://localhost:8202"
    ),
    "parking-availability": os.getenv(
        "PARKING_AVAILABILITY_SERVICE_URL", "http://localhost:8301"
    ),
    "parking-billing": os.getenv(
        "PARKING_BILLING_SERVICE_URL", "http://localhost:8302"
    ),
}
TIMEOUT_SECONDS = float(os.getenv("DOWNSTREAM_TIMEOUT_SECONDS", "5"))
FRONTEND_ORIGINS = [
    origin.strip()
    for origin in os.getenv("FRONTEND_ORIGINS", "http://localhost:8000").split(",")
    if origin.strip()
]

app = FastAPI(title="ServiceUniverse Gateway", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-Request-ID"],
    expose_headers=["X-Request-ID"],
)
app.include_router(water_billing.router)
app.include_router(gas_fault.router)
app.include_router(attraction_reservation.router)
app.include_router(library_account.router)
app.include_router(parking_availability.router)
app.include_router(parking_billing.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "healthy",
        "service": "gateway",
        "version": "0.1.0",
    }


async def check_service(
    client: httpx.AsyncClient, slug: str, base_url: str
) -> tuple[str, dict[str, str]]:
    try:
        response = await client.get(f"{base_url.rstrip('/')}/health")
        response.raise_for_status()
        payload = response.json()
        return slug, {
            "status": payload.get("status", "healthy"),
            "service": payload.get("service", slug),
            "version": payload.get("version", "unknown"),
        }
    except (httpx.HTTPError, ValueError) as error:
        return slug, {
            "status": "unavailable",
            "service": slug,
            "detail": type(error).__name__,
        }


@app.get("/api/v1/health")
async def platform_health(request: Request) -> dict[str, object]:
    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    timeout = httpx.Timeout(TIMEOUT_SECONDS)
    async with httpx.AsyncClient(timeout=timeout) as client:
        results = await asyncio.gather(
            *(
                check_service(client, slug, service_url)
                for slug, service_url in SERVICE_URLS.items()
            )
        )
    services = dict(results)
    all_healthy = all(item["status"] == "healthy" for item in services.values())
    return {
        "success": True,
        "data": {
            "gateway": {"status": "healthy", "version": "0.1.0"},
            "services": services,
            "overall_status": "healthy" if all_healthy else "degraded",
        },
        "message": "Platform health check completed.",
        "meta": {"request_id": request_id},
    }
