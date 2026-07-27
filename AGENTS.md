# ServiceUniverse agent instructions

These instructions apply to the whole repository. Human contributors and AI
assistants follow the same integration rules.

## Start every task here

1. Read `.team-role` if it exists.
2. Read `docs/TASKS.md` and locate that role's owned paths and hand-offs.
3. Read `docs/ARCHITECTURE.md`, `API_CONVENTION.md`, and the target service README.
4. Read `docs/INTEGRATION_PLAYBOOK.md` before changing a shared contract, Gateway,
   shared frontend code, Compose, or CI.
5. Inspect the current branch and working tree before editing.

If `.team-role` is missing, do not guess the contributor's identity. Ask the human
to run `python scripts/select_role.py <A|B|C|D|E|LEADER>`.

## Repository scope

This repository contains executable code, build configuration, API contracts,
tests, analytics scripts, sample data, and technical runbooks. The final report,
meeting reports, BSRL, BPMN, semantic annotations, ArchiMate, and SoaML are
maintained in the team's external report workspace.

Code, API names, schemas, comments intended for delivery, and user-facing UI copy
must be English. Temporary team discussion may be Chinese.

## Architecture rules

- The platform contains six business services.
- Exactly three are selected for full microservice implementation:
  `water-billing`, `attraction-reservation`, and `parking-availability`.
- The shared browser UI calls the Gateway, not service ports directly.
- Services never import another service's source code or read another service's
  database.
- Service addresses come from environment variables.
- Contract changes happen before dependent Gateway or frontend changes.
- `contracts/catalog.json` is the source of truth for provider/service names,
  owners, ports, and selected-microservice labels.

Running a service in a separate Compose process does not by itself make it one of
the three selected microservices.

## Change boundaries

- Work inside the paths owned by the current role.
- Changes to `contracts/`, `gateway/`, shared frontend files, `compose.yaml`,
  dependencies, or CI require an integration note in the pull request and Leader
  review.
- Service-specific frontend work belongs in
  `frontend/templates/services/<service-slug>.html` and optional matching asset
  files. Do not duplicate the shared header, footer, tokens, or navigation.
- Never silently rename endpoints, JSON fields, statuses, activity names, ports,
  or service slugs.
- Preserve unrelated changes in a dirty working tree.

## Required verification

Run before requesting review:

```bash
python -m ruff check .
python -m pytest
docker compose config
```

For integration-affecting changes, also run:

```bash
docker compose up --build
python scripts/smoke_test.py
```

## Definition of done

A task is done only when its contract, implementation, validation, tests,
service-specific README, Gateway integration, and frontend integration are
consistent where applicable. Record commands and results in the pull request.
Do not commit secrets, `.env`, `.team-role`, databases, virtual environments, or
generated analytics results.
