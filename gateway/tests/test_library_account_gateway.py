import asyncio
from typing import Any

import httpx
from fastapi.testclient import TestClient

from gateway.app import main
from gateway.app.routers import library_account

client = TestClient(main.app)


def account_payload() -> dict[str, Any]:
    return {
        "account_id": "LIB-TEST-001",
        "status": "active",
        "card": {"card_number": "CARD-TEST-001"},
        "borrowing": {"items_on_loan": 0},
    }


def test_create_membership_wraps_success_and_forwards_request_id(
    monkeypatch: Any,
) -> None:
    captured: dict[str, Any] = {}

    async def fake_request(
        method: str,
        path: str,
        payload: dict[str, Any] | None,
        request_id: str,
    ) -> tuple[int, dict[str, Any]]:
        captured.update(
            method=method,
            path=path,
            payload=payload,
            request_id=request_id,
        )
        return 201, account_payload()

    monkeypatch.setattr(library_account, "request_library_service", fake_request)
    response = client.post(
        "/api/v1/library-memberships",
        json={"citizen_id": "CIT-TEST"},
        headers={"X-Request-ID": "library-request-001"},
    )

    assert response.status_code == 201
    assert response.json()["success"] is True
    assert response.json()["data"]["account_id"] == "LIB-TEST-001"
    assert response.json()["meta"]["request_id"] == "library-request-001"
    assert response.headers["X-Request-ID"] == "library-request-001"
    assert captured["path"] == "/api/v1/library-memberships"


def test_get_account_wraps_downstream_error(monkeypatch: Any) -> None:
    async def fake_request(
        _method: str,
        _path: str,
        _payload: dict[str, Any] | None,
        _request_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return 404, {
            "error": {
                "code": "LIBRARY_ACCOUNT_NOT_FOUND",
                "message": "The requested library account was not found.",
                "details": None,
            }
        }

    monkeypatch.setattr(library_account, "request_library_service", fake_request)
    response = client.get("/api/v1/library-accounts/LIB-MISSING")

    assert response.status_code == 404
    assert response.json()["success"] is False
    assert response.json()["error"]["code"] == "LIBRARY_ACCOUNT_NOT_FOUND"


def test_update_account_forwards_patch(monkeypatch: Any) -> None:
    captured: dict[str, Any] = {}

    async def fake_request(
        method: str,
        path: str,
        payload: dict[str, Any] | None,
        _request_id: str,
    ) -> tuple[int, dict[str, Any]]:
        captured.update(method=method, path=path, payload=payload)
        return 200, account_payload()

    monkeypatch.setattr(library_account, "request_library_service", fake_request)
    response = client.patch(
        "/api/v1/library-accounts/LIB-TEST-001",
        json={"preferred_language": "zh"},
    )

    assert response.status_code == 200
    assert captured == {
        "method": "PATCH",
        "path": "/api/v1/library-accounts/LIB-TEST-001",
        "payload": {"preferred_language": "zh"},
    }


def test_downstream_500_is_converted_to_bad_gateway(monkeypatch: Any) -> None:
    async def fake_request(
        _method: str,
        _path: str,
        _payload: dict[str, Any] | None,
        _request_id: str,
    ) -> tuple[int, dict[str, Any]]:
        return 500, {"error": {"code": "INTERNAL_ERROR"}}

    monkeypatch.setattr(library_account, "request_library_service", fake_request)
    response = client.get("/api/v1/library-accounts/LIB-TEST-001")

    assert response.status_code == 502
    assert response.json()["success"] is False
    assert response.json()["error"]["code"] == "LIBRARY_SERVICE_UPSTREAM_ERROR"


def test_invalid_downstream_json_is_a_bad_gateway(monkeypatch: Any) -> None:
    class FakeAsyncClient:
        async def __aenter__(self) -> Any:
            return self

        async def __aexit__(self, *_args: object) -> None:
            return None

        async def request(self, *_args: object, **_kwargs: object) -> httpx.Response:
            return httpx.Response(200, text="not-json")

    monkeypatch.setattr(httpx, "AsyncClient", lambda **_kwargs: FakeAsyncClient())
    status_code, payload = asyncio.run(
        library_account.request_library_service(
            "GET",
            "/api/v1/library-accounts/LIB-TEST-001",
            None,
            "request-001",
        )
    )
    assert status_code == 502
    assert payload["error"]["code"] == "INVALID_DOWNSTREAM_RESPONSE"
