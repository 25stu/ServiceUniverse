from importlib import import_module

import pytest
from fastapi.testclient import TestClient

SERVICE_MODULES = [
    ("services.water_billing.app.main", "water-billing"),
    ("services.gas_fault.app.main", "gas-fault"),
    ("services.attraction_reservation.app.main", "attraction-reservation"),
    ("services.library_account.app.main", "library-account"),
    ("services.parking_availability.app.main", "parking-availability"),
    ("services.parking_billing.app.main", "parking-billing"),
]


@pytest.mark.parametrize(("module_name", "service_slug"), SERVICE_MODULES)
def test_service_health(module_name: str, service_slug: str) -> None:
    module = import_module(module_name)
    response = TestClient(module.app).get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": service_slug,
        "version": "0.1.0",
    }
