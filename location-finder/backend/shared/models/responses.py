from typing import Any

from pydantic import BaseModel, Field

from shared.constants import TransportMode, RangeType
from shared.models.location import (
    Coordinates,
    Location,
    CandidateLocation,
)


class GeocodingResponse(BaseModel):
    locations: list[Location] = Field(default_factory=list)


class DiscoveryResponse(BaseModel):
    origin: Location

    transport_mode: TransportMode
    range_type: RangeType
    range_value: int = Field(gt=0)

    isochrone: dict[str, Any]

    candidates: list[CandidateLocation] = Field(
        default_factory=list
    )

    total_candidates: int = Field(ge=0)

    warnings: list[str] = Field(default_factory=list)


class RouteResponse(BaseModel):
    origin: Coordinates
    destination: Coordinates

    transport_mode: TransportMode

    distance_m: float = Field(ge=0)
    duration_seconds: float = Field(ge=0)

    geometry: dict[str, Any]

    warnings: list[str] = Field(default_factory=list)


class HealthResponse(BaseModel):
    api_available: bool
    worker_available: bool