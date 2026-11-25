from pydantic import BaseModel, Field, model_validator

from shared.constants import (
    TransportMode,
    RangeType,
    SortBy,
    LocationCategory,
    DEFAULT_CATEGORIES,
    DEFAULT_RANGE_SECONDS,
    DEFAULT_RESULTS,
    MAX_RESULTS,
    MAX_TIME_SECONDS,
    MAX_DISTANCE_METERS,
    MAX_POI_CATEGORIES,
)
from shared.models.location import Coordinates, Location


class DiscoveryRequest(BaseModel):
    origin: Location

    transport_mode: TransportMode = TransportMode.CAR

    range_type: RangeType = RangeType.TIME
    range_value: int = Field(
        default=DEFAULT_RANGE_SECONDS,
        gt=0,
    )

    categories: list[LocationCategory] = Field(
        default_factory=lambda: list(DEFAULT_CATEGORIES),
        min_length=1,
        max_length=MAX_POI_CATEGORIES,
    )

    max_results: int = Field(
        default=DEFAULT_RESULTS,
        ge=1,
        le=MAX_RESULTS,
    )

    sort_by: SortBy = SortBy.DURATION

    @model_validator(mode="after")
    def validate_search_preferences(self) -> "DiscoveryRequest":
        if self.range_type == RangeType.TIME:
            max_range = MAX_TIME_SECONDS[self.transport_mode]

            if self.range_value > max_range:
                raise ValueError(
                    f"Maximum travel time for {self.transport_mode} "
                    f"is {max_range // 60} minutes."
                )

        elif self.range_type == RangeType.DISTANCE:
            if self.range_value > MAX_DISTANCE_METERS:
                raise ValueError(
                    f"Maximum travel distance is "
                    f"{MAX_DISTANCE_METERS // 1000} km."
                )

        if len(self.categories) != len(set(self.categories)):
            raise ValueError("Location categories must be unique.")

        return self


class RouteRequest(BaseModel):
    origin: Coordinates
    destination: Coordinates

    transport_mode: TransportMode = TransportMode.CAR