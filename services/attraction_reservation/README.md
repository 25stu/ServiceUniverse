# Attraction Recommendation and Reservation

- Owner: Member C
- Port: `8201`
- Classification: selected microservice
- Gateway module: `gateway/app/routers/attraction_reservation.py`
- Frontend view: `frontend/templates/services/attraction-reservation.html`

Minimum workflow:

1. list or recommend attractions using meaningful criteria;
2. create and retrieve a reservation;
3. reject capacity conflicts and invalid reservation transitions.

This service must own its data, configuration, Dockerfile, tests, and API contract
before final delivery.

```bash
python -m uvicorn services.attraction_reservation.app.main:app --reload --port 8201
```

Verify: <http://localhost:8201/health>
