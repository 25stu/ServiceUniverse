from fastapi import FastAPI

app = FastAPI(
    title="Public Library Membership and Account Service",
    version="0.1.0",
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "healthy",
        "service": "library-account",
        "version": "0.1.0",
    }


@app.get("/api/v1/service-info")
async def service_info() -> dict[str, str]:
    return {
        "service": "library-account",
        "owner": "D",
        "implementation": "business_service",
        "status": "scaffold",
    }
