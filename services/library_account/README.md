# Public Library Membership and Account

- Owner: Member D
- Port: `8202`
- Classification: business service
- Gateway module: `gateway/app/routers/library_account.py`
- Frontend view: `frontend/templates/services/library-account.html`

Minimum workflow:

1. create a library membership;
2. retrieve membership and account information;
3. expose representative borrowing or account-standing information;
4. return clear validation and not-found errors.

```bash
python -m uvicorn services.library_account.app.main:app --reload --port 8202
```

Verify: <http://localhost:8202/health>
