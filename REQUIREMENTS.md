# ServiceUniverse executable-system requirements

This repository covers project construction, source code, integration, tests,
analytics scripts, and demonstration assets. Formal report and modelling artefacts
are maintained externally.

## Required platform

- one coherent citizen-facing frontend;
- one API Gateway;
- six executable business services from three providers;
- full microservice implementation for Water Billing, Attraction Reservation, and
  Parking Availability;
- repeatable Gas Fault and Parking Billing process analytics;
- deterministic demonstration data;
- unit, contract, integration, and end-to-end validation.

## Required behaviour for every business service

- FastAPI application;
- `GET /health`;
- published API contract;
- meaningful query and business operations defined in `docs/TASKS.md`;
- Pydantic request and response validation;
- repeatable seed/demo data;
- explicit error handling;
- core business-rule tests;
- service-local run instructions.

## Additional requirements for the three selected microservices

- single, coherent business responsibility;
- independent configuration and data store;
- no sibling-service imports or database access;
- service-local Dockerfile and dependency boundary before final delivery;
- independent build, start, stop, test, and demonstration;
- health checks, automated tests, and clear contracts.

## Integration requirements

- the browser calls the Gateway for business data;
- the Gateway reads downstream addresses from environment variables;
- downstream calls use timeouts and request IDs;
- Gateway failures use the standard error envelope;
- contract changes are reviewed before dependent implementation changes;
- `docker compose up --build` starts the integrated system;
- `python scripts/smoke_test.py` verifies all entry points.

## Definition of done

A feature is complete when:

1. its contract and examples are current;
2. implementation is in the role-owned path;
3. validation, errors, and state transitions are tested;
4. Gateway and frontend integration are complete where applicable;
5. Ruff and pytest pass;
6. Compose remains valid and the smoke test passes;
7. run instructions and known limitations are updated;
8. a reviewer can reproduce the result from a clean clone.

See `docs/ARCHITECTURE.md`, `docs/TASKS.md`, and
`docs/INTEGRATION_PLAYBOOK.md` for the authoritative design and workflow.
