from fastapi.testclient import TestClient

from frontend.app.main import app

client = TestClient(app)


def test_home_lists_all_providers() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "Municipal Utilities Authority" in response.text
    assert "Municipal Culture &amp; Recreation Services" in response.text
    assert "City Parking Management Center" in response.text


def test_provider_page_lists_two_services() -> None:
    response = client.get("/providers/municipal-utilities")

    assert response.status_code == 200
    assert "Water Billing and Payment" in response.text
    assert "Gas Fault Reporting and Repair Tracking" in response.text


def test_unknown_provider_returns_404() -> None:
    response = client.get("/providers/not-a-provider")

    assert response.status_code == 404
