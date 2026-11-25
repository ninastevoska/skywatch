from typing import Any

from shapely.geometry import Polygon, MultiPolygon

from shared.constants import CATEGORY_IDS, RangeType, SortBy
from shared.models.location import Coordinates, CandidateLocation
from shared.models.requests import DiscoveryRequest
from worker.services.geometry import (
    contains_coordinates,
    straight_line_distance_m,
)


# Reverse mapping from API category IDs to application categories.
CATEGORY_BY_ID = {
    category_id: category
    for category, category_id in CATEGORY_IDS.items()
}


def parse_candidates(
    response: dict[str, Any],
    origin: Coordinates,
) -> list[CandidateLocation]:
    """Convert POI features into candidate location models."""

    candidates = []

    for feature in response.get("features", []):
        geometry = feature.get("geometry") or {}
        properties = feature.get("properties") or {}

        if geometry.get("type") != "Point":
            continue

        longitude, latitude = geometry["coordinates"]

        coordinates = Coordinates(
            latitude=latitude,
            longitude=longitude,
        )

        categories = []

        for category_id in properties.get("category_ids", {}):
            category = CATEGORY_BY_ID.get(int(category_id))

            if category is not None:
                categories.append(category)

        if not categories:
            continue

        osm_id = properties["osm_id"]
        osm_type = properties["osm_type"]
        osm_tags = properties.get("osm_tags") or {}

        candidate = CandidateLocation(
            id=f"{osm_type}:{osm_id}",
            osm_id=osm_id,
            osm_type=osm_type,
            coordinates=coordinates,
            name=osm_tags.get("name"),
            categories=categories,
            osm_tags=osm_tags,
            straight_line_distance_m=straight_line_distance_m(
                origin,
                coordinates,
            ),
        )

        candidates.append(candidate)

    return candidates


def deduplicate_candidates(
    candidates: list[CandidateLocation],
) -> list[CandidateLocation]:
    """Merge candidates with the same OSM identifier."""

    unique_candidates: dict[str, CandidateLocation] = {}

    for candidate in candidates:
        existing = unique_candidates.get(candidate.id)

        if existing is None:
            unique_candidates[candidate.id] = (
                candidate.model_copy(deep=True)
            )
            continue

        existing.categories = list(
            dict.fromkeys(
                existing.categories + candidate.categories
            )
        )

        existing.osm_tags.update(candidate.osm_tags)

        if existing.name is None:
            existing.name = candidate.name

    return list(unique_candidates.values())


def filter_by_geometry(
    candidates: list[CandidateLocation],
    geometry: Polygon | MultiPolygon,
) -> list[CandidateLocation]:
    """Keep candidates inside or on the boundary of an area."""

    return [
        candidate
        for candidate in candidates
        if contains_coordinates(
            geometry,
            candidate.coordinates,
        )
    ]


def filter_by_range(
    candidates: list[CandidateLocation],
    request: DiscoveryRequest,
) -> list[CandidateLocation]:
    """Keep reachable candidates within the requested travel range."""

    filtered = []

    for candidate in candidates:
        if (
            candidate.travel_distance_m is None
            or candidate.travel_duration_seconds is None
        ):
            continue

        if request.range_type == RangeType.TIME:
            value = candidate.travel_duration_seconds
        else:
            value = candidate.travel_distance_m

        if value <= request.range_value:
            filtered.append(candidate)

    return filtered


def sort_candidates(
    candidates: list[CandidateLocation],
    sort_by: SortBy,
) -> list[CandidateLocation]:
    """Sort candidates by travel duration or distance."""

    if sort_by == SortBy.DURATION:
        attribute = "travel_duration_seconds"
    else:
        attribute = "travel_distance_m"

    def sort_key(candidate: CandidateLocation) -> float:
        value = getattr(candidate, attribute)

        return value if value is not None else float("inf")

    return sorted(candidates, key=sort_key)