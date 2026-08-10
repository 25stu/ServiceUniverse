from fastapi.testclient import TestClient

from frontend.app.main import app

client = TestClient(app)


def test_parking_availability_page_has_live_workspace() -> None:
    response = client.get("/services/parking-availability")

    assert response.status_code == 200
    assert "Public parking lots" in response.text
    assert "parking-availability.js" in response.text
    assert "This route is ready for the service owner" not in response.text


def test_parking_billing_page_has_session_workflow() -> None:
    response = client.get("/services/parking-billing")

    assert response.status_code == 200
    assert "Start a session" in response.text
    assert "Find a session" in response.text
    assert "parking-billing.js" in response.text
