from pathlib import Path

from fastapi.testclient import TestClient

from services.parking_availability.app.main import create_app


def make_client(tmp_path: Path) -> TestClient:
    database_path = tmp_path / "availability-test.db"
    return TestClient(create_app(f"sqlite:///{database_path}"))


def test_lists_seeded_parking_lots(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        response = client.get("/api/v1/parking-lots")

    assert response.status_code == 200
    assert len(response.json()) == 3
    assert response.json()[0]["availability_status"] in {
        "available",
        "limited",
        "full",
    }


def test_get_unknown_parking_lot_returns_stable_error(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        response = client.get("/api/v1/parking-lots/UNKNOWN")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "PARKING_LOT_NOT_FOUND"


def test_updates_availability_deterministically(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        response = client.patch(
            "/api/v1/parking-lots/LOT-CENTRAL-001/availability",
            json={"available_spaces": 21},
        )
        repeated = client.patch(
            "/api/v1/parking-lots/LOT-CENTRAL-001/availability",
            json={"available_spaces": 21},
        )

    assert response.status_code == 200
    assert response.json()["available_spaces"] == 21
    assert repeated.status_code == 200
    assert repeated.json()["available_spaces"] == 21


def test_rejects_availability_above_capacity(tmp_path: Path) -> None:
    with make_client(tmp_path) as client:
        response = client.patch(
            "/api/v1/parking-lots/LOT-CENTRAL-001/availability",
            json={"available_spaces": 241},
        )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "AVAILABILITY_EXCEEDS_CAPACITY"
