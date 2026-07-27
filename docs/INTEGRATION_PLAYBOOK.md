# Feature integration playbook

This is the standard path from an individual service change to the shared system.

## 1. Identify the role and owned path

```bash
python scripts/select_role.py B
git switch develop
git pull origin develop
git switch -c feature/gas-submit-fault
```

Read `.team-role`, `docs/TASKS.md`, `AGENTS.md`, and the service README before
editing.

## 2. Define the contract first

Before frontend or Gateway code, agree on:

- resource URI and HTTP method;
- request and response fields;
- required versus optional fields;
- allowed states and state transitions;
- success status code;
- error codes;
- at least one success and one failure example.

Add the OpenAPI/JSON Schema and examples under `contracts/`. If another member's
work is affected, open an Issue and request Leader review before implementation.

## 3. Implement inside the service

Use the existing internal layers:

```text
app/api/           HTTP routes only
app/schemas/       Pydantic request and response models
app/models/        persistence models
app/repositories/  database access
app/services/      business rules and workflow
```

Do not put business rules in the Gateway or Jinja template. Do not import another
service's code or database.

## 4. Add service tests

Test:

- the normal business path;
- invalid input;
- resource not found;
- illegal state transition or conflict;
- one service-specific edge case.

Run only the service tests while iterating, then run the full suite.

## 5. Connect the Gateway

Edit only the role-owned module in `gateway/app/routers/`. The Gateway should:

- read the downstream address from configuration;
- forward `X-Request-ID`;
- use an explicit timeout;
- translate downstream failures into the platform error envelope;
- avoid duplicating business validation.

Do not change `gateway/app/main.py` unless shared startup behaviour must change.

## 6. Connect the shared frontend

Edit:

```text
frontend/templates/services/<service-slug>.html
```

Add service-specific CSS or JavaScript only when needed. Reuse the shared header,
navigation, typography, colours, focus states, form patterns, and error language.
Browser requests go through the Gateway public URL.

Do not copy `base.html` or create another independent navigation bar.

## 7. Verify integration

```bash
python -m ruff check .
python -m pytest
docker compose config
docker compose up --build
python scripts/smoke_test.py
```

Manually complete the affected citizen workflow from the shared homepage.

## 8. Open a focused pull request

Push the feature branch and fill in every relevant PR section. Include:

- role and service;
- Issue/contract reference;
- endpoints or schemas changed;
- test commands and results;
- screenshot for UI work;
- known limitations;
- required reviewer.

The Leader merges to `develop` after contract owner and cross-review approval.

## Breaking changes

Never merge only one side of a breaking change. The contract, service, Gateway,
frontend, tests, examples, and affected analytics activity names must land in one
coordinated change or in a documented compatibility sequence.
