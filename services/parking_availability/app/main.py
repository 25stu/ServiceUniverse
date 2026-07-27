from fastapi import FastAPI

app = FastAPI(title="Public Parking Availability Service", version="0.1.0")


@app.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "healthy",
        "service": "parking-availability",
        "version": "0.1.0",
    }


@app.get("/api/v1/service-info")
async def service_info() -> dict[str, str]:
    return {
        "service": "parking-availability",
        "owner": "E",
        "implementation": "selected_microservice",
        "status": "scaffold",
    }
