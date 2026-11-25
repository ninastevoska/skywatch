from fastapi import APIRouter, HTTPException, Query

from app.clients.geocoding import GeocodingClient
from shared.errors import ExternalAPIError
from shared.models.responses import GeocodingResponse


router = APIRouter(prefix="/api", tags=["Locations"])

geocoding_client = GeocodingClient()


@router.get("/locations", response_model=GeocodingResponse)
async def search_locations(
    name: str = Query(min_length=2, max_length=100),
    limit: int = Query(default=10, ge=1, le=20),
) -> GeocodingResponse:
    """Search for geographic locations by name."""

    name = name.strip()

    if len(name) < 2:
        raise HTTPException(
            status_code=422,
            detail="Location name must contain at least two characters.",
        )

    try:
        locations = await geocoding_client.search(
            name=name,
            limit=limit,
        )

    except ExternalAPIError as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "code": exc.code,
                "message": "Unable to retrieve geographic locations.",
            },
        ) from exc

    return GeocodingResponse(locations=locations)