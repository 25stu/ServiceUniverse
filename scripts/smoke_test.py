from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request

ENDPOINTS = {
    "frontend": "http://localhost:8000/health",
    "gateway": "http://localhost:8080/api/v1/health",
    "water-billing": "http://localhost:8101/health",
    "gas-fault": "http://localhost:8102/health",
    "attraction-reservation": "http://localhost:8201/health",
    "library-account": "http://localhost:8202/health",
    "parking-availability": "http://localhost:8301/health",
    "parking-billing": "http://localhost:8302/health",
}


def wait_for_endpoint(name: str, url: str) -> bool:
    for attempt in range(1, 16):
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                payload = json.load(response)
            status = payload.get("status") or payload.get("data", {}).get(
                "overall_status"
            )
            print(f"[OK]   {name:<24} {status}")
            return True
        except (urllib.error.URLError, TimeoutError, ValueError):
            if attempt < 15:
                time.sleep(2)
    print(f"[FAIL] {name:<24} no healthy response after 30 seconds")
    return False


def main() -> None:
    failed = [
        name
        for name, url in ENDPOINTS.items()
        if not wait_for_endpoint(name, url)
    ]

    if failed:
        print(f"\nSmoke test failed: {', '.join(failed)}")
        sys.exit(1)
    print("\nAll ServiceUniverse entry points responded.")


if __name__ == "__main__":
    main()
