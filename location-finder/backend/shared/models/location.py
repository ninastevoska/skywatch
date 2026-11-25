from pydantic import BaseModel, Field

from shared.constants import LocationCategory


class Coordinates(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)

    def to_geojson(self) -> list[float]:
        """Return coordinates in GeoJSON order."""
        return [self.longitude, self.latitude]


class Location(BaseModel):
    coordinates: Coordinates

    name: str | None = None
    country: str | None = None
    region: str | None = None
    timezone: str | None = None


class CandidateLocation(BaseModel):
    id: str

    osm_id: int = Field(gt=0)
    osm_type: int

    coordinates: Coordinates

    name: str | None = None
    categories: list[LocationCategory] = Field(min_length=1)
    osm_tags: dict[str, str] = Field(default_factory=dict)

    straight_line_distance_m: float | None = Field(
        default=None, ge=0
    )

    travel_distance_m: float | None = Field(
        default=None, ge=0
    )

    travel_duration_seconds: float | None = Field(
        default=None, ge=0
    )

    snapped_coordinates: Coordinates | None = None

    snapped_distance_m: float | None = Field(
        default=None, ge=0
    )