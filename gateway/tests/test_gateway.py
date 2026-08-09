import httpx
import pytest
from fastapi.testclient import TestClient

from gateway.app import main
from gateway.app.routers import water_billing

client = TestClient(main.app)


def test_gateway_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["service"] == "gateway"


def test_platform_health_uses_envelope(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def healthy_service(
        _client: httpx.AsyncClient, slug: str, _url: str
    ) -> tuple[str, dict[str, str]]:
        return slug, {"status": "healthy", "service": slug, "version": "0.1.0"}

    monkeypatch.setattr(main, "check_service", healthy_service)
    response = client.get(
        "/api/v1/health",
        headers={"X-Request-ID": "test-request-id"},
    )

    payload = response.json()
    assert response.status_code == 200
    assert payload["success"] is True
    assert payload["data"]["overall_status"] == "healthy"
    assert len(payload["data"]["services"]) == 6
    assert payload["meta"]["request_id"] == "test-request-id"


def test_water_bills_are_forwarded_in_public_envelope(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def downstream_response(
        _method: str,
        _path: str,
        _request_id: str,
        _payload: dict[str, object] | None = None,
    ) -> httpx.Response:
        return httpx.Response(
            200,
            json=[{"bill_id": "BILL-1001", "status": "unpaid"}],
            request=httpx.Request("GET", "http://water-billing/api/v1/bills"),
        )

    monkeypatch.setattr(water_billing, "request_water_service", downstream_response)
    response = client.get(
        "/api/v1/bills?citizen_id=CITIZEN-1001",
        headers={"X-Request-ID": "water-request-id"},
    )

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["data"][0]["bill_id"] == "BILL-1001"
    assert response.headers["X-Request-ID"] == "water-request-id"


def test_water_payment_conflict_uses_public_error_envelope(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def downstream_response(
        _method: str,
        _path: str,
        _request_id: str,
        _payload: dict[str, object] | None = None,
    ) -> httpx.Response:
        return httpx.Response(
            409,
            json={
                "code": "BILL_ALREADY_PAID",
                "message": "This bill has already been paid and cannot be paid again.",
            },
            request=httpx.Request("POST", "http://water-billing/api/v1/payments"),
        )

    monkeypatch.setattr(water_billing, "request_water_service", downstream_response)
    response = client.post(
        "/api/v1/payments",
        json={"bill_id": "BILL-1001", "payment_method": "card"},
    )

    assert response.status_code == 409
    assert response.json()["success"] is False
    assert response.json()["error"]["code"] == "BILL_ALREADY_PAID"


def test_water_receipt_pdf_is_forwarded_as_a_download(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def downstream_pdf(
        _path: str, _request_id: str
    ) -> tuple[int, bytes, str | None, dict[str, object] | None]:
        return (
            200,
            b"%PDF-1.4\\nexample",
            'attachment; filename="water-payment-RCT-1002-DEMO.pdf"',
            None,
        )

    monkeypatch.setattr(water_billing, "request_water_pdf", downstream_pdf)
    response = client.get("/api/v1/bills/BILL-1002/receipt.pdf")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.headers["content-disposition"].endswith("RCT-1002-DEMO.pdf\"")
    assert response.content.startswith(b"%PDF-1.4")
