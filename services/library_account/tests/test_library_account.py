from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from services.library_account.app.main import app

client = TestClient(app)


def application(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "citizen_id": f"CIT-{uuid4().hex[:10]}",
        "full_name": "Morgan Lee",
        "date_of_birth": "1994-06-18",
        "email": "morgan.lee@example.com",
        "phone": "+61 412 345 678",
        "preferred_language": "en",
        "card_type": "digital",
        "home_branch": "Central Library",
        "identity_verified": True,
        "terms_accepted": True,
        "payment_confirmed": True,
    }
    payload.update(overrides)
    return payload


def test_create_and_retrieve_membership() -> None:
    create_response = client.post("/api/v1/library-memberships", json=application())

    assert create_response.status_code == 201
    account = create_response.json()
    assert account["status"] == "active"
    assert account["card"]["delivery_status"] == "issued"
    assert account["borrowing"]["borrowing_allowed"] is True
    assert account["payment"]["amount_minor"] == 500
    assert account["payment"]["status"] == "paid"
    assert account["payment"]["payment_reference"].startswith("SIM-PAY-")

    get_response = client.get(f"/api/v1/library-accounts/{account['account_id']}")
    assert get_response.status_code == 200
    assert get_response.json()["citizen_id"] == account["citizen_id"]


def test_chinese_confirmation_and_physical_card() -> None:
    response = client.post(
        "/api/v1/library-memberships",
        json=application(
            preferred_language="zh",
            card_type="physical",
            mailing_address="18 Crown Street, Wollongong NSW 2500",
        ),
    )

    assert response.status_code == 201
    assert "会员申请成功" in response.json()["confirmation_notification"]
    assert response.json()["card"]["delivery_status"] == "ready_for_delivery"


@pytest.mark.parametrize(
    ("overrides", "error_code"),
    [
        ({"identity_verified": False}, "IDENTITY_NOT_VERIFIED"),
        ({"terms_accepted": False}, "TERMS_NOT_ACCEPTED"),
        ({"payment_confirmed": False}, "PAYMENT_REQUIRED"),
        ({"citizen_id": "CIT-RESTRICTED"}, "ACCOUNT_RESTRICTED"),
    ],
)
def test_business_preconditions_are_enforced(
    overrides: dict[str, object], error_code: str
) -> None:
    response = client.post("/api/v1/library-memberships", json=application(**overrides))

    assert response.status_code in {400, 409}
    assert response.json()["error"]["code"] == error_code


def test_duplicate_membership_is_rejected() -> None:
    payload = application()
    assert client.post("/api/v1/library-memberships", json=payload).status_code == 201

    response = client.post("/api/v1/library-memberships", json=payload)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "MEMBERSHIP_ALREADY_EXISTS"


def test_validation_error_is_safe_and_structured() -> None:
    response = client.post(
        "/api/v1/library-memberships",
        json=application(email="not-an-email"),
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert response.json()["error"]["details"][0]["field"] == ""


def test_update_contact_information() -> None:
    created = client.post("/api/v1/library-memberships", json=application()).json()

    response = client.patch(
        f"/api/v1/library-accounts/{created['account_id']}",
        json={"email": "new.address@example.com", "preferred_language": "zh"},
    )

    assert response.status_code == 200
    assert response.json()["email"] == "new.address@example.com"
    assert response.json()["preferred_language"] == "zh"


def test_unknown_account_returns_not_found() -> None:
    response = client.get("/api/v1/library-accounts/LIB-NOT-FOUND")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "LIBRARY_ACCOUNT_NOT_FOUND"


def test_payment_is_virtual_and_contains_no_card_data() -> None:
    response = client.post("/api/v1/library-memberships", json=application())

    assert response.status_code == 201
    payment = response.json()["payment"]
    assert payment["amount_minor"] == 500
    assert payment["currency"] == "AUD"
    assert payment["status"] == "paid"
    assert payment["payment_reference"].startswith("SIM-PAY-")
    assert "card_number" not in payment
