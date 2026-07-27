from fastapi import FastAPI

app = FastAPI(title="Water Billing and Payment Service", version="0.1.0")


@app.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "healthy",
        "service": "water-billing",
        "version": "0.1.0",
    }


@app.get("/api/v1/service-info")
async def service_info() -> dict[str, str]:
    return {
        "service": "water-billing",
        "owner": "A",
        "implementation": "selected_microservice",
        "status": "scaffold",
    }
