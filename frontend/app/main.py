from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BASE_DIR.parent
CATALOG_PATH = PROJECT_ROOT / "contracts" / "catalog.json"


def load_catalog() -> dict[str, Any]:
    with CATALOG_PATH.open(encoding="utf-8") as catalog_file:
        return json.load(catalog_file)


def find_provider(catalog: dict[str, Any], slug: str) -> dict[str, Any] | None:
    return next(
        (provider for provider in catalog["providers"] if provider["slug"] == slug),
        None,
    )


def find_service(
    catalog: dict[str, Any], slug: str
) -> tuple[dict[str, Any], dict[str, Any]] | None:
    for provider in catalog["providers"]:
        service = next(
            (item for item in provider["services"] if item["slug"] == slug),
            None,
        )
        if service:
            return provider, service
    return None


app = FastAPI(
    title="ServiceUniverse Frontend",
    version="0.1.0",
    docs_url=None,
    redoc_url=None,
)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


def template_context(request: Request, **extra: Any) -> dict[str, Any]:
    return {
        "request": request,
        "catalog": load_catalog(),
        "gateway_public_url": os.getenv(
            "GATEWAY_PUBLIC_URL", "http://localhost:8080"
        ).rstrip("/"),
        **extra,
    }


@app.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "healthy",
        "service": "frontend",
        "version": "0.1.0",
    }


@app.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context=template_context(request),
    )


@app.get("/providers/{provider_slug}", response_class=HTMLResponse)
async def provider_page(request: Request, provider_slug: str) -> HTMLResponse:
    catalog = load_catalog()
    provider = find_provider(catalog, provider_slug)
    if provider is None:
        raise HTTPException(status_code=404, detail="Provider not found")
    return templates.TemplateResponse(
        request=request,
        name="provider.html",
        context=template_context(request, provider=provider),
    )


@app.get("/services/{service_slug}", response_class=HTMLResponse)
async def service_page(request: Request, service_slug: str) -> HTMLResponse:
    catalog = load_catalog()
    result = find_service(catalog, service_slug)
    if result is None:
        raise HTTPException(status_code=404, detail="Service not found")
    provider, service = result
    return templates.TemplateResponse(
        request=request,
        name=f"services/{service_slug}.html",
        context=template_context(request, provider=provider, service=service),
    )
