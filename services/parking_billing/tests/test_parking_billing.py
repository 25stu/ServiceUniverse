from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi.testclient import TestClient

from services.parking_billing.app.main import create_app


def make_client(tmp_path: Path) -> TestClient:
    return TestClient(create_app(f"sqlite:///{tmp_path / 'billing-test.db'}"))


def session_payload(vehicle_plate: str = "ABC 123") -> dict[str, str]:
    return {
        "citizen_id": "CITIZEN-001",
        "vehicle_plate": vehicle_plate,
        "parking_lot_id": "LOT-CENTRAL-001",
        "started_at": "2026-08-09T08:00:00Z",
    }


def test_create_get_end_and_pay_session(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        created = client.post("/api/v1/parking-sessions", json=session_payload())
        session_id = created.json()["session_id"]
        fetched = client.get(f"/api/v1/parking-sessions/{session_id}")
        ended = client.post(
            f"/api/v1/parking-sessions/{session_id}/end",
            json={"ended_at": "2026-08-09T09:15:00Z"},
        )
        paid = client.post(
            "/api/v1/parking-payments",
            json={"session_id": session_id, "payment_method": "card"},
        )
        events = client.get(f"/api/v1/parking-sessions/{session_id}/events")

    assert created.status_code == 201
    assert fetched.json()["status"] == "active"
    assert ended.json()["duration_minutes"] == 75
    assert ended.json()["amount_minor"] == 800
    assert paid.status_code == 201
    assert paid.json()["amount_minor"] == 800
    assert [event["activity"] for event in events.json()] == [
        "Register Parking Entry",
        "Close Parking Session",
        "Calculate Parking Fee",
        "Initiate Payment",
        "Confirm Payment",
    ]


def test_rejects_duplicate_active_vehicle_session(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        client.post("/api/v1/parking-sessions", json=session_payload())
        response = client.post("/api/v1/parking-sessions", json=session_payload())

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "ACTIVE_SESSION_EXISTS"


def test_rejects_payment_before_session_ends(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        created = client.post(
            "/api/v1/parking-sessions", json=session_payload("EARLY 1")
        )
        response = client.post(
            "/api/v1/parking-payments",
            json={"session_id": created.json()["session_id"], "payment_method": "card"},
        )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "SESSION_NOT_BILLABLE"


def test_rejects_duplicate_payment(tmp_path: Path) -> None:
    start = datetime.now(UTC) - timedelta(hours=2)
    with make_client(tmp_path) as client:
        created = client.post(
            "/api/v1/parking-sessions",
            json={
                **session_payload("PAID 1"),
                "started_at": start.isoformat(),
            },
        )
        session_id = created.json()["session_id"]
        client.post(f"/api/v1/parking-sessions/{session_id}/end", json={})
        client.post(
            "/api/v1/parking-payments",
            json={"session_id": session_id, "payment_method": "digital_wallet"},
        )
        duplicate = client.post(
            "/api/v1/parking-payments",
            json={"session_id": session_id, "payment_method": "digital_wallet"},
        )

    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "SESSION_ALREADY_PAID"


def test_unknown_session_returns_not_found(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        response = client.get("/api/v1/parking-sessions/UNKNOWN")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "PARKING_SESSION_NOT_FOUND"
