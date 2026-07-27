# Gas Fault Reporting and Repair Tracking

- Owner: Member B
- Port: `8102`
- Classification: business service
- Gateway module: `gateway/app/routers/gas_fault.py`
- Frontend view: `frontend/templates/services/gas-fault.html`
- Analytics workspace: `analytics/gas_fault/`

Minimum workflow:

1. submit a fault report;
2. retrieve the report and current repair status;
3. perform valid status transitions;
4. generate or simulate a reproducible process event log.

Freeze BPMN activity names before generating the final log.

```bash
python -m uvicorn services.gas_fault.app.main:app --reload --port 8102
```

Verify: <http://localhost:8102/health>
