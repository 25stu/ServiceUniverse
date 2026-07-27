import json
from pathlib import Path

CATALOG_PATH = Path(__file__).resolve().parents[1] / "contracts" / "catalog.json"


def test_catalog_has_three_providers_and_six_unique_services() -> None:
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    providers = catalog["providers"]
    services = [
        service
        for provider in providers
        for service in provider["services"]
    ]

    assert len(providers) == 3
    assert all(len(provider["services"]) == 2 for provider in providers)
    assert len(services) == 6
    assert len({service["slug"] for service in services}) == 6
    assert len({service["port"] for service in services}) == 6


def test_exactly_three_services_are_selected_microservices() -> None:
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    selected = [
        service["slug"]
        for provider in catalog["providers"]
        for service in provider["services"]
        if service["implementation"] == "selected_microservice"
    ]

    assert selected == [
        "water-billing",
        "attraction-reservation",
        "parking-availability",
    ]
