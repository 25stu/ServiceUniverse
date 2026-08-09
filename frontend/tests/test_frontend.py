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


def test_library_page_contains_complete_member_workflow() -> None:
    response = client.get("/services/library-account")

    assert response.status_code == 200
    assert 'data-membership-form' in response.text
    assert 'data-account-search' in response.text
    assert 'data-account-update' in response.text
    assert "POST /api/v1/library-memberships" in response.text
    assert 'name="payment_confirmed"' in response.text
    assert "simulated AUD 5.00" in response.text
    assert "/static/js/library-account.js" in response.text


def test_water_billing_page_contains_citizen_workflow() -> None:
    response = client.get("/services/water-billing")

    assert response.status_code == 200
    assert "Review and pay a water bill" in response.text
    assert 'data-water-bill-form' in response.text
    assert "/static/js/water-billing.js" in response.text


def test_water_bill_detail_and_receipt_pages_render() -> None:
    detail = client.get("/services/water-billing/bills/BILL-1001")
    receipt = client.get("/services/water-billing/bills/BILL-1002/receipt")

    assert detail.status_code == 200
    assert 'data-water-bill-detail' in detail.text
    assert "/static/js/water-bill-detail.js" in detail.text
    assert receipt.status_code == 200
    assert 'data-water-receipt-page' in receipt.text
    assert "/static/js/water-bill-receipt.js" in receipt.text
