# API contracts

This directory is the integration boundary between service owners, the Gateway,
the shared frontend, tests, and analytics.

Before implementing a business endpoint, add:

- `schemas/<service-slug>.openapi.yaml` or focused JSON Schema files;
- one successful request/response example;
- at least one representative error example;
- allowed enum/status values;
- event activity names when the process is analysed.

`catalog.json` is the source of truth for the six service identities and ports.
Only the Leader should merge changes to service slugs, owners, provider grouping,
ports, or selected-microservice labels.
