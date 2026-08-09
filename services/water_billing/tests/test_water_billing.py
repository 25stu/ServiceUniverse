from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from services.water_billing.app import database, main


@pytest.fixture()
def client(tmp_path) -> Generator[TestClient, None, None]:
    database.reset_database_for_testing(f"sqlite:///{tmp_path / 'water_billing.db'}")
    with TestClient(main.app) as test_client:
        yield test_client
    database.configure()


def test_list_bills_for_citizen(client: TestClient) -> None:
    response = client.get("/api/v1/bills", params={"citizen_id": "CITIZEN-1001"})

    assert response.status_code == 200
    assert [bill["bill_id"] for bill in response.json()] == [
        "BILL-1004",
        "BILL-1001",
        "BILL-1002",
        "BILL-1003",
    ]


def test_default_demonstration_citizen_has_current_and_historical_bills(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/bills", params={"citizen_id": "CITIZEN-2001"})
    bills = response.json()

    assert response.status_code == 200
    assert [bill["bill_id"] for bill in bills] == [
        "BILL-2004",
        "BILL-2001",
        "BILL-2002",
        "BILL-2003",
    ]
    assert {bill["status"] for bill in bills} == {"paid", "unpaid"}


def test_bill_detail_includes_usage_and_charge_breakdown(client: TestClient) -> None:
    response = client.get("/api/v1/bills/BILL-1001")
    bill = response.json()

    assert response.status_code == 200
    assert bill["customer_name"] == "Alex Morgan"
    assert bill["meter_number"] == "WTR-2048-77"
    assert bill["water_usage_kl"] == 152
    assert (
        bill["fixed_charge_minor"]
        + bill["consumption_charge_minor"]
        + bill["gst_minor"]
        == bill["amount_minor"]
    )


def test_payment_marks_bill_paid_and_returns_receipt(client: TestClient) -> None:
    response = client.post(
        "/api/v1/payments",
        json={"bill_id": "BILL-1001", "payment_method": "card"},
    )

    payload = response.json()
    assert response.status_code == 201
    assert payload["bill_id"] == "BILL-1001"
    assert payload["status"] == "completed"
    assert payload["receipt_number"].startswith("RCT-")

    bill = client.get("/api/v1/bills/BILL-1001")
    assert bill.json()["status"] == "paid"
    assert bill.json()["paid_at"] is not None

    receipt = client.get(f"/api/v1/payments/{payload['payment_id']}")
    assert receipt.status_code == 200
    assert receipt.json()["receipt_number"] == payload["receipt_number"]

    bill_receipt = client.get("/api/v1/bills/BILL-1001/receipt")
    pdf_receipt = client.get("/api/v1/bills/BILL-1001/receipt.pdf")
    assert bill_receipt.status_code == 200
    assert bill_receipt.json()["payment_id"] == payload["payment_id"]
    assert pdf_receipt.status_code == 200
    assert pdf_receipt.headers["content-type"] == "application/pdf"
    assert pdf_receipt.content.startswith(b"%PDF-1.4")
    assert len(pdf_receipt.content) > 2_000


def test_seeded_paid_bill_has_a_retrievable_receipt(client: TestClient) -> None:
    for bill_id in ("BILL-1002", "BILL-1003", "BILL-2002", "BILL-2003", "BILL-3002"):
        receipt = client.get(f"/api/v1/bills/{bill_id}/receipt")

        assert receipt.status_code == 200
        assert receipt.json()["receipt_number"].startswith("RCT-")


def test_payment_rejects_duplicate_and_paid_bills(client: TestClient) -> None:
    first = client.post(
        "/api/v1/payments",
        json={"bill_id": "BILL-1001", "payment_method": "bank_transfer"},
    )
    duplicate = client.post(
        "/api/v1/payments",
        json={"bill_id": "BILL-1001", "payment_method": "bank_transfer"},
    )
    seeded_paid = client.post(
        "/api/v1/payments",
        json={"bill_id": "BILL-1002", "payment_method": "card"},
    )

    assert first.status_code == 201
    assert duplicate.status_code == 409
    assert duplicate.json()["code"] == "BILL_ALREADY_PAID"
    assert seeded_paid.status_code == 409

    no_receipt = client.get("/api/v1/bills/BILL-2001/receipt")
    assert no_receipt.status_code == 404
    assert no_receipt.json()["code"] == "RECEIPT_NOT_FOUND"


def test_water_service_returns_stable_validation_and_not_found_errors(
    client: TestClient,
) -> None:
    invalid = client.post(
        "/api/v1/payments",
        json={"bill_id": "invalid", "payment_method": "cash"},
    )
    missing = client.get("/api/v1/bills/BILL-9999")

    assert invalid.status_code == 422
    assert invalid.json()["code"] == "VALIDATION_ERROR"
    assert missing.status_code == 404
    assert missing.json()["code"] == "BILL_NOT_FOUND"
