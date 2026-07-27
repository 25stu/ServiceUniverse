from fastapi import FastAPI

app = FastAPI(
    title="Attraction Recommendation and Reservation Service",
    version="0.1.0",
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "healthy",
        "service": "attraction-reservation",
        "version": "0.1.0",
    }


@app.get("/api/v1/service-info")
async def service_info() -> dict[str, str]:
    return {
        "service": "attraction-reservation",
        "owner": "C",
        "implementation": "selected_microservice",
        "status": "scaffold",
    }
