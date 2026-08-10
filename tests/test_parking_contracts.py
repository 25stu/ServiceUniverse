from pathlib import Path

import yaml

CONTRACTS = Path(__file__).resolve().parents[1] / "contracts" / "schemas"


def test_parking_availability_contract_has_required_operations() -> None:
    contract = yaml.safe_load(
        (CONTRACTS / "parking-availability.openapi.yaml").read_text(encoding="utf-8")
    )

    assert contract["openapi"] == "3.1.0"
    assert "/api/v1/parking-lots" in contract["paths"]
    assert (
        contract["paths"]["/api/v1/parking-lots/{lot_id}/availability"]["patch"]
        ["operationId"]
        == "updateParkingLotAvailability"
    )


def test_parking_billing_contract_has_session_and_payment_operations() -> None:
    contract = yaml.safe_load(
        (CONTRACTS / "parking-billing.openapi.yaml").read_text(encoding="utf-8")
    )

    assert "/api/v1/parking-sessions" in contract["paths"]
    assert "/api/v1/parking-payments" in contract["paths"]
    assert "/api/v1/parking-sessions/{session_id}/events" in contract["paths"]
