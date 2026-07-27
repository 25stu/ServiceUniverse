# Team tasks and code ownership

This file maps each team role to executable repository work. Report and modelling
deliverables are intentionally out of scope here.

## Leader

Owned paths:

- shared files in `frontend/`;
- `gateway/app/main.py` and shared Gateway utilities;
- `compose.yaml`, root Docker configuration, dependencies, and CI;
- `contracts/catalog.json`;
- root technical documentation.

Responsibilities:

- maintain the runnable integration baseline;
- review every breaking contract or shared UI change;
- keep `main` stable and `develop` runnable;
- run weekly integration, smoke tests, and release packaging.

## Member A — Water Billing and Payment

Owned paths:

- `services/water_billing/`;
- `gateway/app/routers/water_billing.py`;
- `frontend/templates/services/water-billing.html`;
- Water contract and examples under `contracts/`.

Minimum code scope:

- retrieve a citizen's bill;
- pay an eligible unpaid bill;
- retrieve payment result or receipt;
- reject duplicate payment and illegal state transitions;
- independent data store and Dockerfile because this is a selected microservice.

Hand-off: notify Leader when the contract changes; provide stable endpoints to the
shared frontend and demonstration workflow.

## Member B — Gas Fault Reporting and Repair Tracking

Owned paths:

- `services/gas_fault/`;
- `gateway/app/routers/gas_fault.py`;
- `frontend/templates/services/gas-fault.html`;
- `analytics/gas_fault/`;
- Gas contract and examples under `contracts/`.

Minimum code scope:

- create a fault report;
- retrieve a report and its repair status;
- update status through valid repair stages;
- generate or simulate event logs whose activities match the frozen BPMN activity
  dictionary.

Hand-off: provide reproducible Gas Fault logs and analysis commands.

## Member C — Attraction Recommendation and Reservation

Owned paths:

- `services/attraction_reservation/`;
- `gateway/app/routers/attraction_reservation.py`;
- `frontend/templates/services/attraction-reservation.html`;
- `analytics/parking_billing/mining/` and interpreted results;
- Attraction contract and examples under `contracts/`.

Minimum code scope:

- list or recommend attractions from meaningful criteria;
- create and retrieve a reservation;
- enforce capacity and reservation-state rules;
- independent data store and Dockerfile because this is a selected microservice.

Hand-off from E: receive the frozen Parking Billing activity dictionary and raw
event log before mining. Never overwrite raw logs during cleaning.

## Member D — Public Library Membership and Account

Owned paths:

- `services/library_account/`;
- `gateway/app/routers/library_account.py`;
- `frontend/templates/services/library-account.html`;
- Library contract and examples under `contracts/`.

Minimum code scope:

- create a library membership;
- retrieve membership/account information;
- expose representative borrowing or account standing information;
- implement validation and useful error states.

Repository review role: check cross-service naming and API consistency. ArchiMate
and SoaML work remains in the external report workspace.

## Member E — City Parking Management Center

Owned paths:

- `services/parking_availability/`;
- `services/parking_billing/`;
- both parking Gateway route modules;
- both parking service templates;
- `analytics/parking_billing/simulation_or_export/` and raw event logs;
- Parking contracts and examples under `contracts/`.

Parking Availability minimum code scope:

- list parking locations and available capacity;
- retrieve one parking location;
- provide deterministic capacity-change/demo behaviour;
- independent data store and Dockerfile because this is a selected microservice.

Parking Billing minimum code scope:

- create or retrieve a parking session;
- end a session and calculate the charge;
- pay an eligible charge;
- emit or simulate the process events required by C.

Hand-off to C: freeze activity names, lifecycle values, normal paths, exceptional
paths, and log schema before formal mining.

## Shared files and review

No member owns a shared file exclusively enough to bypass review. Changes to these
paths require Leader review:

- `contracts/catalog.json`;
- `API_CONVENTION.md`;
- `frontend/templates/base.html`;
- `frontend/static/css/site.css`;
- `gateway/app/main.py`;
- `compose.yaml`;
- dependency files;
- `.github/workflows/`.

Use the pull request template to state the affected owner, contract impact,
commands run, and integration result.
