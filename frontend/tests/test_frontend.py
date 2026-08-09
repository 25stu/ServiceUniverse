from fastapi.testclient import TestClient

from frontend.app.main import app

client = TestClient(app)


def test_home_lists_all_providers() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "Municipal Utilities Authority" in response.text
    assert "Municipal Culture &amp; Recreation Services" in response.text
    assert "City Parking Management Center" in response.text
    assert response.text.count('href="/services/') == 6
    assert "Everyday services." not in response.text


def test_provider_page_lists_two_services() -> None:
    response = client.get("/providers/municipal-utilities")

    assert response.status_code == 200
    assert "Water Billing and Payment" in response.text
    assert "Gas Fault Reporting and Repair Tracking" in response.text


def test_unknown_provider_returns_404() -> None:
    response = client.get("/providers/not-a-provider")

    assert response.status_code == 404


def test_gas_fault_page_contains_role_entries() -> None:
    response = client.get("/services/gas-fault")

    assert response.status_code == 200
    assert 'id="citizen-entry-form"' in response.text
    assert 'id="admin-entry-button"' in response.text
    assert "/static/css/gas-fault.css" in response.text
    assert "/static/js/gas-fault.js" in response.text


def test_gas_fault_user_workspace_contains_personal_reports() -> None:
    response = client.get("/services/gas-fault/user")

    assert response.status_code == 200
    assert 'id="fault-report-form"' in response.text
    assert 'id="user-report-list"' in response.text
    assert 'id="status-update-form"' not in response.text
    assert 'id="cancel-report-button"' in response.text


def test_gas_fault_admin_workspace_contains_all_reports_and_update() -> None:
    response = client.get("/services/gas-fault/admin")

    assert response.status_code == 200
    assert 'id="admin-report-list"' in response.text
    assert 'id="status-update-form"' in response.text
    assert 'id="cancel-report-button"' not in response.text
    assert "Demonstration role" in response.text
