from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.events import router as events_router
from app.api.recommendations import router as recommendations_router
from app.config import get_settings


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description=(
        "AI-powered astronomical observation recommendations "
        "and astronomical event discovery."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

app.include_router(events_router)
app.include_router(recommendations_router)


@app.get("/api/health", tags=["System"])
def health_check() -> dict[str, str]:
    """Check whether the SkyWatch AI backend is running."""

    return {
        "status": "ok",
        "service": settings.app_name,
    }
