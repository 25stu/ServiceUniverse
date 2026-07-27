# Parking Billing and Payment

- Owner: Member E
- Port: `8302`
- Classification: business service
- Gateway module: `gateway/app/routers/parking_billing.py`
- Frontend view: `frontend/templates/services/parking-billing.html`
- Analytics hand-off: `analytics/parking_billing/`

Minimum workflow:

1. create or retrieve a parking session;
2. end a session and calculate its charge;
3. pay an eligible charge;
4. emit or simulate the process events required by Member C.

Freeze activity and lifecycle names with Member C before the final log.

```bash
python -m uvicorn services.parking_billing.app.main:app --reload --port 8302
```

Verify: <http://localhost:8302/health>
