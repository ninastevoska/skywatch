import uvicorn

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.api.health import router as health_router
from app.api.locations import router as locations_router
from app.api.discovery import router as discovery_router
from app.api.routes import router as routes_router
from shared.config import PROJECT_ROOT


app = FastAPI(
    title="SkyWatch Location Finder",
    description="Discover reachable locations for astronomical observations.",
    version="1.0.0",
)


# Register REST API routers.
app.include_router(health_router)
app.include_router(locations_router)
app.include_router(discovery_router)
app.include_router(routes_router)


# Serve the frontend after registering all API routes.
frontend_directory = PROJECT_ROOT / "frontend"

app.mount(
    "/",
    StaticFiles(
        directory=frontend_directory,
        html=True,
    ),
    name="frontend",
)


def main() -> None:
    """Start the Location Finder API server."""

    uvicorn.run(
        app,
        host=settings.app_host,
        port=settings.app_port,
        log_level="info",
    )


if __name__ == "__main__":
    main()