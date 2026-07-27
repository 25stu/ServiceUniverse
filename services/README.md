# Business service implementation guide

Each child directory is owned by one role and follows the same internal shape:

```text
app/main.py       FastAPI startup and router registration
app/api/          HTTP route handlers
app/schemas/      Pydantic API models
app/models/       persistence models
app/repositories/ data access
app/services/     business rules
tests/            service-local tests
data/             deterministic seed/demo data
```

The six directories represent six business services. Only Water Billing,
Attraction Reservation, and Parking Availability are selected for full
microservice implementation. See `docs/ARCHITECTURE.md`.

Do not create imports between sibling service directories.
