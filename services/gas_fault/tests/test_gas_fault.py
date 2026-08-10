from fastapi.testclient import TestClient

from services.gas_fault.app.main import create_app


def make_client(tmp_path) -> TestClient:
    database_url = f"sqlite:///{(tmp_path / 'gas-fault-test.sqlite3').as_posix()}"
    return TestClient(create_app(database_url))


def valid_report() -> dict[str, str]:
    return {
        "citizen_id": "CITIZEN-001",
        "reporter_name": "Alex Chen",
        "contact_phone": "0400 000 000",
        "address": "12 King Street",
        "description": "A strong gas smell is coming from the kitchen meter.",
        "severity": "high",
    }


def create_report(client: TestClient) -> dict[str, object]:
    response = client.post(
        "/api/v1/fault-reports",
        json=valid_report(),
        headers={"X-Citizen-ID": "CITIZEN-001"},
    )
    assert response.status_code == 201
    return response.json()


def test_create_and_retrieve_fault_report(tmp_path) -> None:
    client = make_client(tmp_path)
    created = create_report(client)

    assert str(created["report_id"]).startswith("FAULT-")
    assert created["status"] == "reported"
    assert created["history"][0]["activity"] == "Submit Fault Report"

    response = client.get(
        f"/api/v1/fault-reports/{created['report_id']}",
        headers={"X-Citizen-ID": "CITIZEN-001"},
    )
    assert response.status_code == 200
    assert response.json() == created


def test_create_rejects_invalid_input(tmp_path) -> None:
    client = make_client(tmp_path)
    payload = valid_report()
    payload["description"] = "short"

    response = client.post(
        "/api/v1/fault-reports",
        json=payload,
        headers={"X-Citizen-ID": "CITIZEN-001"},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_unknown_report_returns_stable_error(tmp_path) -> None:
    client = make_client(tmp_path)

    response = client.get(
        "/api/v1/fault-reports/FAULT-UNKNOWN",
        headers={"X-Citizen-ID": "CITIZEN-001"},
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "FAULT_REPORT_NOT_FOUND"


def test_legal_status_update_adds_history(tmp_path) -> None:
    client = make_client(tmp_path)
    report = create_report(client)

    response = client.patch(
        f"/api/v1/fault-reports/{report['report_id']}/status",
        json={
            "status": "assigned",
            "resource": "Dispatch Officer",
            "note": "Assigned to Gas Repair Team 1.",
        },
        headers={"X-User-Role": "gas_operator"},
    )

    payload = response.json()
    assert response.status_code == 200
    assert payload["status"] == "assigned"
    assert len(payload["history"]) == 2
    assert payload["history"][-1]["activity"] == "Assign Repair Team"


def test_illegal_status_update_is_rejected_without_mutation(tmp_path) -> None:
    client = make_client(tmp_path)
    report = create_report(client)
    report_id = report["report_id"]

    response = client.patch(
        f"/api/v1/fault-reports/{report_id}/status",
        json={"status": "closed", "resource": "Dispatch Officer"},
        headers={"X-User-Role": "gas_operator"},
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == (
        "INVALID_FAULT_STATUS_TRANSITION"
    )
    unchanged = client.get(
        f"/api/v1/fault-reports/{report_id}",
        headers={"X-Citizen-ID": "CITIZEN-001"},
    ).json()
    assert unchanged["status"] == "reported"
    assert len(unchanged["history"]) == 1


def test_citizen_lists_only_their_reports_and_cannot_read_another(tmp_path) -> None:
    client = make_client(tmp_path)
    own_report = create_report(client)
    other_payload = valid_report()
    other_payload["citizen_id"] = "CITIZEN-002"
    other = client.post(
        "/api/v1/fault-reports",
        json=other_payload,
        headers={"X-Citizen-ID": "CITIZEN-002"},
    ).json()

    response = client.get(
        "/api/v1/fault-reports",
        headers={"X-Citizen-ID": "CITIZEN-001"},
    )

    assert response.status_code == 200
    assert [item["report_id"] for item in response.json()] == [
        own_report["report_id"]
    ]
    denied = client.get(
        f"/api/v1/fault-reports/{other['report_id']}",
        headers={"X-Citizen-ID": "CITIZEN-001"},
    )
    assert denied.status_code == 403
    assert denied.json()["error"]["code"] == "FAULT_REPORT_ACCESS_DENIED"


def test_administrator_lists_all_reports_and_citizen_cannot_update(tmp_path) -> None:
    client = make_client(tmp_path)
    report = create_report(client)

    listing = client.get(
        "/api/v1/fault-reports",
        headers={"X-User-Role": "gas_operator"},
    )
    denied = client.patch(
        f"/api/v1/fault-reports/{report['report_id']}/status",
        json={"status": "assigned", "resource": "Citizen"},
        headers={"X-User-Role": "citizen"},
    )

    assert listing.status_code == 200
    assert len(listing.json()) == 1
    assert denied.status_code == 403
    assert denied.json()["error"]["code"] == "ADMINISTRATOR_ACCESS_REQUIRED"


def test_citizen_cancels_active_report_and_both_roles_see_timeline(tmp_path) -> None:
    client = make_client(tmp_path)
    report = create_report(client)
    report_id = report["report_id"]
    for next_status in ("assigned", "inspection_in_progress"):
        response = client.patch(
            f"/api/v1/fault-reports/{report_id}/status",
            json={"status": next_status, "resource": "Gas Repair Team 1"},
            headers={"X-User-Role": "gas_operator"},
        )
        assert response.status_code == 200

    cancelled = client.post(
        f"/api/v1/fault-reports/{report_id}/cancel",
        headers={"X-Citizen-ID": "CITIZEN-001"},
    )

    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"
    assert cancelled.json()["history"][-1]["activity"] == "Cancel Fault Report"
    citizen_view = client.get(
        f"/api/v1/fault-reports/{report_id}",
        headers={"X-Citizen-ID": "CITIZEN-001"},
    ).json()
    admin_view = client.get(
        f"/api/v1/fault-reports/{report_id}",
        headers={"X-User-Role": "gas_operator"},
    ).json()
    assert citizen_view["history"] == admin_view["history"]
    assert admin_view["history"][-1]["status"] == "cancelled"


def test_citizen_cannot_cancel_another_citizens_report(tmp_path) -> None:
    client = make_client(tmp_path)
    report = create_report(client)

    response = client.post(
        f"/api/v1/fault-reports/{report['report_id']}/cancel",
        headers={"X-Citizen-ID": "CITIZEN-002"},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FAULT_REPORT_ACCESS_DENIED"


def test_completed_report_cannot_be_cancelled(tmp_path) -> None:
    client = make_client(tmp_path)
    report_id = create_report(client)["report_id"]
    for next_status in (
        "assigned",
        "inspection_in_progress",
        "repair_in_progress",
        "resolved",
    ):
        response = client.patch(
            f"/api/v1/fault-reports/{report_id}/status",
            json={"status": next_status, "resource": "Gas Repair Team 1"},
            headers={"X-User-Role": "gas_operator"},
        )
        assert response.status_code == 200

    response = client.post(
        f"/api/v1/fault-reports/{report_id}/cancel",
        headers={"X-Citizen-ID": "CITIZEN-001"},
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "FAULT_REPORT_CANNOT_BE_CANCELLED"
