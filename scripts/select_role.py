from __future__ import annotations

import argparse
from pathlib import Path

VALID_ROLES = {"A", "B", "C", "D", "E", "LEADER"}
PROJECT_ROOT = Path(__file__).resolve().parents[1]
ROLE_FILE = PROJECT_ROOT / ".team-role"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Record this clone's ServiceUniverse team role for humans and AI."
    )
    parser.add_argument("role", choices=sorted(VALID_ROLES))
    args = parser.parse_args()

    role = args.role.upper()
    ROLE_FILE.write_text(f"ROLE={role}\n", encoding="utf-8")
    print(f"Local role set to {role}. This file is ignored by Git.")
    print("Next: read docs/TASKS.md and docs/INTEGRATION_PLAYBOOK.md.")


if __name__ == "__main__":
    main()
