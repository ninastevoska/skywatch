"""Expose SkyWatch tourism statistics through a REST API."""

from contextlib import asynccontextmanager

import pandas as pd
from fastapi import Depends, FastAPI, HTTPException, Query, Request

from src.px_fetcher import fetch_px
from src.px_parser import parse_px
from src.tourism_service import TourismDataError, TourismService

from pathlib import Path
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

def load_tourism_service() -> TourismService:
    """Download, parse, and prepare the tourism dataset."""
    content = fetch_px()
    data, _metadata = parse_px(content)
    return TourismService(data)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load the remote PC-Axis dataset once at application startup."""
    print("Loading tourism data from SURS...")

    app.state.tourism_service = load_tourism_service()

    print("Tourism data loaded successfully.")

    yield

    app.state.tourism_service = None


app = FastAPI(
    title="SkyWatch AstroDestination Explorer",
    description="Tourism statistics for Slovenian municipalities.",
    lifespan=lifespan,
)


STATIC_DIR = Path(__file__).resolve().parent / "static"

app.mount(
    "/static",
    StaticFiles(directory=STATIC_DIR),
    name="static",
)


@app.get("/", include_in_schema=False)
def dashboard():
    """Serve the AstroDestination Explorer web interface."""
    return FileResponse(STATIC_DIR / "index.html")


def get_tourism_service(request: Request) -> TourismService:
    """Return the initialized tourism service."""
    service = getattr(request.app.state, "tourism_service", None)

    if service is None:
        raise HTTPException(
            status_code=503,
            detail="Tourism data is not available.",
        )

    return service


def to_json_records(data: pd.DataFrame) -> list[dict]:
    """Convert a DataFrame to records with JSON-safe values."""
    records = []

    for record in data.to_dict(orient="records"):
        cleaned = {}

        for key, value in record.items():
            if pd.isna(value):
                cleaned[key] = None
            elif hasattr(value, "item"):
                cleaned[key] = value.item()
            else:
                cleaned[key] = value

        records.append(cleaned)

    return records


@app.exception_handler(TourismDataError)
async def tourism_error_handler(
    request: Request, exc: TourismDataError
):
    """Return a readable response for invalid tourism selections."""
    from fastapi.responses import JSONResponse

    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)},
    )


@app.get("/api/municipalities")
def get_municipalities(
    service: TourismService = Depends(get_tourism_service),
):
    """Return available Slovenian municipalities."""
    municipalities = [
        name for name in service.municipalities()
        if name != "SLOVENIJA"
    ]

    return {"municipalities": municipalities}


@app.get("/api/years")
def get_years(
    municipality: str = Query(min_length=1),
    service: TourismService = Depends(get_tourism_service),
):
    """Return available years for the selected municipality."""
    return {
        "municipality": municipality,
        "years": service.available_years(municipality),
    }


@app.get("/api/monthly")
def get_monthly(
    municipality: str = Query(min_length=1),
    year: int = Query(ge=1900, le=2200),
    service: TourismService = Depends(get_tourism_service),
):
    """Return monthly overnight stays for a municipality."""
    data = service.monthly_overnights(municipality, year)

    return {
        "municipality": municipality,
        "year": year,
        "months": to_json_records(data),
    }


@app.get("/api/compare")
def compare_municipalities(
    first: str = Query(min_length=1),
    second: str = Query(min_length=1),
    year: int = Query(ge=1900, le=2200),
    service: TourismService = Depends(get_tourism_service),
):
    """Compare monthly overnight stays between two municipalities."""
    data = service.compare_municipalities(
        first, second, year
    )

    return {
        "first": first,
        "second": second,
        "year": year,
        "months": to_json_records(data),
    }


@app.get("/api/extremes")
def get_extreme_months(
    municipality: str = Query(min_length=1),
    year: int = Query(ge=1900, le=2200),
    service: TourismService = Depends(get_tourism_service),
):
    """Return the months with most and fewest overnight stays."""
    return service.extreme_months(municipality, year)


@app.get("/api/trends")
def get_annual_trends(
    municipality: str = Query(min_length=1),
    service: TourismService = Depends(get_tourism_service),
):
    """Return annual totals and completeness indicators."""
    data = service.annual_trends(municipality)

    return {
        "municipality": municipality,
        "years": to_json_records(data),
    }
