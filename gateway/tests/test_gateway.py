import httpx
import pytest
from fastapi.testclient import TestClient

from gateway.app import main

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
