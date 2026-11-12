from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.conditions import router as conditions_router


app = FastAPI(
    title="SkyWatch Observation Conditions",
    version="1.0.0",
)

FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"

app.include_router(conditions_router)

app.mount(
    "/static",
    StaticFiles(directory=FRONTEND_DIR),
    name="static",
)


@app.get("/")
async def index():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/health")
async def health():
    return {"status": "ok"}
