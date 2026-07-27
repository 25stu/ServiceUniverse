from fastapi import FastAPI

app = FastAPI(
    title="Gas Fault Reporting and Repair Tracking Service",
    version="0.1.0",
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "healthy",
        "service": "gas-fault",
        "version": "0.1.0",
    }


@app.get("/api/v1/service-info")
async def service_info() -> dict[str, str]:
    return {
        "service": "gas-fault",
        "owner": "B",
        "implementation": "business_service",
        "status": "scaffold",
    }
