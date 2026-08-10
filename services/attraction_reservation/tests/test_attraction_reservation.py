from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from services.attraction_reservation.app import main


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    database_url = f"sqlite:///{(tmp_path / 'attraction.db').as_posix()}"
    with TestClient(main.create_app(database_url)) as test_client:
        yield test_client


def test_recommends_available_attractions_for_visit_date(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/v1/attractions",
        params={
            "visit_date": "2026-08-06",
            "visitor_count": 2,
            "district": "central",
            "recommend": "true",
        },
    )

    payload = response.json()
    assert response.status_code == 200
    assert [item["attraction_id"] for item in payload] == ["ATTR-1003", "ATTR-1001"]
    assert payload[0]["available_capacity"] == 60


def test_creates_and_reads_reservation(client: TestClient) -> None:
    create_response = client.post(
        "/api/v1/reservations",
        json={
            "attraction_id": "ATTR-1001",
            "citizen_id": "CIT-1000",
            "visit_date": "2026-08-06",
            "visitor_count": 3,
        },
    )

    created = create_response.json()
    read_response = client.get(
        f"/api/v1/reservations/{created['reservation_id']}"
    )

    assert create_response.status_code == 201
    assert created["status"] == "confirmed"
    assert read_response.status_code == 200
    assert read_response.json()["visitor_count"] == 3


def test_rejects_capacity_conflict(client: TestClient) -> None:
    responses = []
    for index in range(6):
        responses.append(
            client.post(
                "/api/v1/reservations",
                json={
                    "attraction_id": "ATTR-1003",
                    "citizen_id": f"CIT-100{index}",
                    "visit_date": "2026-08-06",
                    "visitor_count": 10,
                },
            )
        )
    conflict_response = client.post(
        "/api/v1/reservations",
        json={
            "attraction_id": "ATTR-1003",
            "citizen_id": "CIT-2000",
            "visit_date": "2026-08-06",
            "visitor_count": 1,
        },
    )

    assert [response.status_code for response in responses] == [201] * 6
    assert conflict_response.status_code == 409
    assert conflict_response.json()["detail"]["code"] == "CAPACITY_CONFLICT"


def test_rejects_invalid_status_transition(client: TestClient) -> None:
    create_response = client.post(
        "/api/v1/reservations",
        json={
            "attraction_id": "ATTR-1002",
            "citizen_id": "CIT-1000",
            "visit_date": "2026-08-06",
            "visitor_count": 1,
        },
    )
    reservation_id = create_response.json()["reservation_id"]
    transition_response = client.patch(
        f"/api/v1/reservations/{reservation_id}/status",
        json={"status": "pending"},
    )

    assert transition_response.status_code == 409
    assert transition_response.json()["detail"]["code"] == (
        "INVALID_RESERVATION_STATUS"
    )


def test_reservation_persists_across_application_restart(tmp_path: Path) -> None:
    database_url = f"sqlite:///{(tmp_path / 'persistent.db').as_posix()}"
    with TestClient(main.create_app(database_url)) as first_client:
        create_response = first_client.post(
            "/api/v1/reservations",
            json={
                "attraction_id": "ATTR-1001",
                "citizen_id": "CIT-PERSIST",
                "visit_date": "2026-08-06",
                "visitor_count": 2,
            },
        )
        reservation_id = create_response.json()["reservation_id"]

    with TestClient(main.create_app(database_url)) as restarted_client:
        response = restarted_client.get(
            f"/api/v1/reservations/{reservation_id}"
        )

    assert response.status_code == 200
    assert response.json()["citizen_id"] == "CIT-PERSIST"
