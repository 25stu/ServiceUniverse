import httpx
import pytest
from fastapi.testclient import TestClient

from gateway.app import main
from gateway.app.routers import gas_fault

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


def test_gas_fault_gateway_wraps_downstream_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeAsyncClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def request(self, method, url, headers, content):
            assert method == "POST"
            assert url.endswith("/api/v1/fault-reports")
            assert headers["X-Request-ID"] == "gateway-test-id"
            assert headers["X-Citizen-ID"] == "CITIZEN-001"
            assert content
            request = httpx.Request(method, url)
            return httpx.Response(
                201,
                request=request,
                json={"report_id": "FAULT-A1B2C3D4", "status": "reported"},
            )

    monkeypatch.setattr(
        gas_fault.httpx,
        "AsyncClient",
        lambda **_kwargs: FakeAsyncClient(),
    )
    response = client.post(
        "/api/v1/fault-reports",
        headers={
            "X-Request-ID": "gateway-test-id",
            "X-Citizen-ID": "CITIZEN-001",
        },
        json={"description": "A valid downstream request body."},
    )

    payload = response.json()
    assert response.status_code == 201
    assert payload["success"] is True
    assert payload["data"]["report_id"] == "FAULT-A1B2C3D4"
    assert payload["meta"]["request_id"] == "gateway-test-id"


def test_gas_fault_gateway_preserves_domain_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeAsyncClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def request(self, method, url, headers, content):
            request = httpx.Request(method, url)
            return httpx.Response(
                404,
                request=request,
                json={
                    "error": {
                        "code": "FAULT_REPORT_NOT_FOUND",
                        "message": "The requested fault report was not found.",
                        "details": None,
                    }
                },
            )

    monkeypatch.setattr(
        gas_fault.httpx,
        "AsyncClient",
        lambda **_kwargs: FakeAsyncClient(),
    )
    response = client.get("/api/v1/fault-reports/FAULT-UNKNOWN")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "FAULT_REPORT_NOT_FOUND"
