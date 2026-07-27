# Public Parking Availability

- Owner: Member E
- Port: `8301`
- Classification: selected microservice
- Gateway module: `gateway/app/routers/parking_availability.py`
- Frontend view: `frontend/templates/services/parking-availability.html`

Minimum workflow:

1. list parking locations and current capacity;
2. retrieve one parking location;
3. provide deterministic capacity-change behaviour for demonstration.

This service must own its data, configuration, Dockerfile, tests, and API contract
before final delivery.

```bash
python -m uvicorn services.parking_availability.app.main:app --reload --port 8301
```

Verify: <http://localhost:8301/health>
