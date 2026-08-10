from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from services.library_account.app.schemas import (
    AccountUpdate,
    LibraryAccount,
    MembershipApplication,
)
from services.library_account.app.service import LibraryDomainError, membership_service

app = FastAPI(
    title="Public Library Membership and Account Service",
    version="0.1.0",
)


@app.exception_handler(LibraryDomainError)
async def handle_domain_error(
    _request: Request, error: LibraryDomainError
) -> JSONResponse:
    return JSONResponse(
        status_code=error.status_code,
        content={
            "error": {
                "code": error.code,
                "message": error.message,
                "details": error.details,
            }
        },
    )


@app.exception_handler(RequestValidationError)
async def handle_validation_error(
    _request: Request, error: RequestValidationError
) -> JSONResponse:
    details: list[dict[str, Any]] = []
    for item in error.errors():
        details.append(
            {
                "field": ".".join(str(part) for part in item["loc"] if part != "body"),
                "message": item["msg"],
            }
        )
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "The membership request contains invalid data.",
                "details": details,
            }
        },
    )


@app.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "healthy",
        "service": "library-account",
        "version": "0.1.0",
    }


@app.get("/api/v1/service-info")
async def service_info() -> dict[str, str]:
    return {
        "service": "library-account",
        "owner": "D",
        "implementation": "business_service",
        "status": "ready",
    }


@app.post(
    "/api/v1/library-memberships",
    response_model=LibraryAccount,
    status_code=201,
)
async def create_membership(application: MembershipApplication) -> LibraryAccount:
    return membership_service.create_membership(application)


@app.get(
    "/api/v1/library-accounts/{account_id}",
    response_model=LibraryAccount,
)
async def get_library_account(account_id: str) -> LibraryAccount:
    return membership_service.get_account(account_id)


@app.patch(
    "/api/v1/library-accounts/{account_id}",
    response_model=LibraryAccount,
)
async def update_library_account(
    account_id: str, update: AccountUpdate
) -> LibraryAccount:
    return membership_service.update_account(account_id, update)
