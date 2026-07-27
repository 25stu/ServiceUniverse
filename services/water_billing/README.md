# Water Billing and Payment

- Owner: Member A
- Port: `8101`
- Classification: selected microservice
- Gateway module: `gateway/app/routers/water_billing.py`
- Frontend view: `frontend/templates/services/water-billing.html`

Minimum workflow:

1. retrieve a bill for a citizen;
2. pay an eligible unpaid bill;
3. retrieve the payment result or receipt;
4. reject duplicate payment and invalid state transitions.

This service must own its data, configuration, Dockerfile, tests, and API contract
before final delivery.

Run the current scaffold:

```bash
python -m uvicorn services.water_billing.app.main:app --reload --port 8101
```

Verify: <http://localhost:8101/health>
