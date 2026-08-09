from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient

from gateway.app import main
from gateway.app.routers import parking_availability, parking_billing

client = TestClient(main.app)


class FakeAsyncClient:
    response_status = 200
    response_json: Any = None

    def __init__(self, **_kwargs: Any) -> None:
        pass

    async def __aenter__(self) -> "FakeAsyncClient":
        return self

    async def __aexit__(self, *_args: Any) -> None:
        return None

    async def request(self, method: str, url: str, **_kwargs: Any) -> httpx.Response:
        request = httpx.Request(method, url)
        return httpx.Response(
            self.response_status,
            json=self.response_json,
            request=request,
        )


def test_parking_availability_gateway_wraps_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    FakeAsyncClient.response_status = 200
    FakeAsyncClient.response_json = [{"lot_id": "LOT-CENTRAL-001"}]
    monkeypatch.setattr(parking_availability.httpx, "AsyncClient", FakeAsyncClient)

    response = client.get(
        "/api/v1/parking-lots", headers={"X-Request-ID": "parking-test"}
    )

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["data"][0]["lot_id"] == "LOT-CENTRAL-001"
    assert response.json()["meta"]["request_id"] == "parking-test"


def test_parking_billing_gateway_preserves_business_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    FakeAsyncClient.response_status = 409
    FakeAsyncClient.response_json = {
        "error": {
            "code": "SESSION_ALREADY_PAID",
            "message": "This parking session has already been paid.",
            "details": None,
        }
    }
    monkeypatch.setattr(parking_billing.httpx, "AsyncClient", FakeAsyncClient)

    response = client.post(
        "/api/v1/parking-payments",
        json={"session_id": "SESSION-1", "payment_method": "card"},
    )

    assert response.status_code == 409
    assert response.json()["success"] is False
    assert response.json()["error"]["code"] == "SESSION_ALREADY_PAID"
