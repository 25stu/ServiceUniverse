# Development environment

## Recommended path: Docker

Install:

- Git;
- Docker Desktop with Docker Compose v2.

Then run:

```bash
git clone <repository-url>
cd ServiceUniverse
python scripts/select_role.py A
docker compose up --build
```

Open <http://localhost:8000>. The first build downloads Python packages and can
take several minutes.

Useful commands:

```bash
docker compose ps
docker compose logs -f gateway
docker compose restart water-billing
docker compose down
```

Do not use `docker compose down -v` unless you intentionally want to remove
development data volumes after they are introduced.

## Local Python path

Use Python 3.11:

```bash
python -m venv .venv
```

PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Bash:

```bash
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
```

Run one component:

```bash
python -m uvicorn services.water_billing.app.main:app --reload --port 8101
```

Run the shared frontend:

```bash
python -m uvicorn frontend.app.main:app --reload --port 8000
```

Run the Gateway:

```bash
python -m uvicorn gateway.app.main:app --reload --port 8080
```

When running locally, each required downstream service must be started in its own
terminal. Docker Compose is preferred for full integration.

## Quality checks

```bash
python -m ruff check .
python -m pytest
docker compose config
```

After starting the platform:

```bash
python scripts/smoke_test.py
```

## Port map

| Component | Port |
|---|---:|
| Frontend | 8000 |
| Gateway | 8080 |
| Water Billing | 8101 |
| Gas Fault | 8102 |
| Attraction Reservation | 8201 |
| Library Account | 8202 |
| Parking Availability | 8301 |
| Parking Billing | 8302 |

Do not silently choose another permanent port. Coordinate changes through
`contracts/catalog.json`, Compose, `.env.example`, and documentation.

## Common problems

### `services must be a mapping`

Your branch probably has an incomplete `compose.yaml`. Restore or merge the current
integration version before continuing.

### Gateway reports all services unavailable

Inside Docker, service URLs must use Compose names such as
`http://water-billing:8101`, not `localhost`. The committed Compose file already
sets these values.

### Browser reports Gateway unavailable

Confirm <http://localhost:8080/health> works and that
`FRONTEND_ORIGINS` includes <http://localhost:8000>.

### A port is already in use

Stop the previous development process or conflicting container. Avoid changing the
shared port map as a local workaround.
