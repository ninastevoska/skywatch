import pytest

from shapely.geometry import Polygon

from shared.constants import (
    CATEGORY_IDS,
    LocationCategory,
    RangeType,
    SortBy,
    TransportMode,
)

from shared.models.location import (
    Coordinates,
    Location,
    CandidateLocation,
)

from shared.models.requests import DiscoveryRequest

from worker.services.candidates import (
    parse_candidates,
    deduplicate_candidates,
    filter_by_geometry,
    filter_by_range,
    sort_candidates,
)


@pytest.fixture
def origin():
    """Create a starting location in Maribor."""

    return Coordinates(
        latitude=46.5547,
        longitude=15.6459,
    )


def create_candidate(
    osm_id=1,
    osm_type=1,
    name="Test location",
    categories=None,
    latitude=46.555,
    longitude=15.645,
    distance=1000,
    duration=600,
    osm_tags=None,
):
    """Create a candidate with configurable properties."""

    return CandidateLocation(
        id=f"{osm_type}:{osm_id}",
        osm_id=osm_id,
        osm_type=osm_type,
        name=name,
        coordinates=Coordinates(
            latitude=latitude,
            longitude=longitude,
        ),
        categories=categories or [
            LocationCategory.VIEWPOINT
        ],
        osm_tags=osm_tags or {},
        travel_distance_m=distance,
        travel_duration_seconds=duration,
    )


def create_poi_feature(
    osm_id=1,
    osm_type=1,
    category_ids=None,
    geometry_type="Point",
    osm_tags=None,
):
    """Create a representative openpoiservice feature."""

    return {
        "type": "Feature",
        "geometry": {
            "type": geometry_type,
            "coordinates": [15.650, 46.560],
        },
        "properties": {
            "osm_id": osm_id,
            "osm_type": osm_type,
            "category_ids": {
                str(category_id): {}
                for category_id in (category_ids or [])
            },
            "osm_tags": osm_tags or {},
        },
    }


# Parsing tests


def test_parse_candidate(origin):
    """Convert a valid POI feature into a candidate."""

    feature = create_poi_feature(
        osm_id=123,
        category_ids=[
            CATEGORY_IDS[LocationCategory.VIEWPOINT],
        ],
        osm_tags={
            "name": "Piramida",
        },
    )

    candidates = parse_candidates(
        {"features": [feature]},
        origin,
    )

    assert len(candidates) == 1

    candidate = candidates[0]

    assert candidate.id == "1:123"
    assert candidate.osm_id == 123
    assert candidate.name == "Piramida"

    assert candidate.coordinates.latitude == 46.560
    assert candidate.coordinates.longitude == 15.650

    assert candidate.categories == [
        LocationCategory.VIEWPOINT
    ]

    assert candidate.straight_line_distance_m > 0


def test_parse_multiple_categories(origin):
    """Preserve all supported categories of a location."""

    feature = create_poi_feature(
        category_ids=[
            CATEGORY_IDS[LocationCategory.VIEWPOINT],
            CATEGORY_IDS[LocationCategory.PEAK],
        ],
    )

    candidates = parse_candidates(
        {"features": [feature]},
        origin,
    )

    assert len(candidates) == 1

    assert set(candidates[0].categories) == {
        LocationCategory.VIEWPOINT,
        LocationCategory.PEAK,
    }


def test_parse_unnamed_candidate(origin):
    """Accept locations without an OSM name."""

    feature = create_poi_feature(
        category_ids=[
            CATEGORY_IDS[LocationCategory.PEAK],
        ],
    )

    candidates = parse_candidates(
        {"features": [feature]},
        origin,
    )

    assert len(candidates) == 1
    assert candidates[0].name is None


def test_ignore_unknown_categories(origin):
    """Ignore locations without supported categories."""

    feature = create_poi_feature(
        category_ids=[999999],
    )

    candidates = parse_candidates(
        {"features": [feature]},
        origin,
    )

    assert candidates == []


def test_ignore_non_point_geometry(origin):
    """Ignore unsupported geometry types."""

    feature = create_poi_feature(
        geometry_type="Polygon",
        category_ids=[
            CATEGORY_IDS[LocationCategory.VIEWPOINT],
        ],
    )

    candidates = parse_candidates(
        {"features": [feature]},
        origin,
    )

    assert candidates == []


# Deduplication tests


def test_deduplicate_candidates():
    """Merge locations with identical OSM identifiers."""

    first = create_candidate(
        osm_id=100,
        categories=[LocationCategory.VIEWPOINT],
        osm_tags={"name": "Piramida"},
    )

    second = create_candidate(
        osm_id=100,
        categories=[LocationCategory.PEAK],
        osm_tags={"natural": "peak"},
    )

    result = deduplicate_candidates([
        first,
        second,
    ])

    assert len(result) == 1

    candidate = result[0]

    assert set(candidate.categories) == {
        LocationCategory.VIEWPOINT,
        LocationCategory.PEAK,
    }

    assert candidate.osm_tags == {
        "name": "Piramida",
        "natural": "peak",
    }

    # Original input objects must remain unchanged.
    assert first.categories == [
        LocationCategory.VIEWPOINT
    ]

    assert first.osm_tags == {
        "name": "Piramida",
    }


def test_deduplicate_preserves_name():
    """Recover a missing name from a duplicate candidate."""

    first = create_candidate(
        osm_id=100,
        name=None,
    )

    second = create_candidate(
        osm_id=100,
        name="Piramida",
    )

    result = deduplicate_candidates([
        first,
        second,
    ])

    assert len(result) == 1
    assert result[0].name == "Piramida"


def test_different_osm_types_are_not_duplicates():
    """Keep distinct OSM objects with the same numeric ID."""

    first = create_candidate(
        osm_id=100,
        osm_type=1,
    )

    second = create_candidate(
        osm_id=100,
        osm_type=2,
    )

    result = deduplicate_candidates([
        first,
        second,
    ])

    assert len(result) == 2


# Geometry filtering tests


def test_filter_by_geometry():
    """Keep candidates inside or on the search area boundary."""

    geometry = Polygon([
        (15.640, 46.550),
        (15.650, 46.550),
        (15.650, 46.560),
        (15.640, 46.560),
        (15.640, 46.550),
    ])

    inside = create_candidate(
        osm_id=1,
        latitude=46.555,
        longitude=15.645,
    )

    outside = create_candidate(
        osm_id=2,
        latitude=47.000,
        longitude=16.000,
    )

    boundary = create_candidate(
        osm_id=3,
        latitude=46.550,
        longitude=15.640,
    )

    result = filter_by_geometry(
        [inside, outside, boundary],
        geometry,
    )

    assert result == [inside, boundary]


# Travel range filtering tests


def test_filter_by_travel_time(origin):
    """Keep candidates within the travel time limit."""

    request = DiscoveryRequest(
        origin=Location(coordinates=origin),
        transport_mode=TransportMode.WALKING,
        range_type=RangeType.TIME,
        range_value=1800,
    )

    within_limit = create_candidate(
        osm_id=1,
        duration=900,
    )

    exact_limit = create_candidate(
        osm_id=2,
        duration=1800,
    )

    exceeds_limit = create_candidate(
        osm_id=3,
        duration=1801,
    )

    result = filter_by_range(
        [within_limit, exact_limit, exceeds_limit],
        request,
    )

    assert result == [
        within_limit,
        exact_limit,
    ]


def test_filter_by_travel_distance(origin):
    """Keep candidates within the travel distance limit."""

    request = DiscoveryRequest(
        origin=Location(coordinates=origin),
        transport_mode=TransportMode.WALKING,
        range_type=RangeType.DISTANCE,
        range_value=5000,
    )

    within_limit = create_candidate(
        osm_id=1,
        distance=3000,
    )

    exact_limit = create_candidate(
        osm_id=2,
        distance=5000,
    )

    exceeds_limit = create_candidate(
        osm_id=3,
        distance=5001,
    )

    result = filter_by_range(
        [within_limit, exact_limit, exceeds_limit],
        request,
    )

    assert result == [
        within_limit,
        exact_limit,
    ]


@pytest.mark.parametrize(
    "distance, duration",
    [
        (None, 600),
        (1000, None),
        (None, None),
    ],
)
def test_filter_unreachable_candidates(
    origin,
    distance,
    duration,
):
    """Exclude candidates with incomplete routing data."""

    request = DiscoveryRequest(
        origin=Location(coordinates=origin),
        range_type=RangeType.TIME,
        range_value=1800,
    )

    candidate = create_candidate(
        distance=distance,
        duration=duration,
    )

    result = filter_by_range(
        [candidate],
        request,
    )

    assert result == []


# Sorting tests


def test_sort_by_duration():
    """Sort candidates by ascending travel duration."""

    first = create_candidate(
        osm_id=1,
        duration=1200,
    )

    second = create_candidate(
        osm_id=2,
        duration=300,
    )

    third = create_candidate(
        osm_id=3,
        duration=600,
    )

    result = sort_candidates(
        [first, second, third],
        SortBy.DURATION,
    )

    assert result == [
        second,
        third,
        first,
    ]


def test_sort_by_distance():
    """Sort candidates by ascending travel distance."""

    first = create_candidate(
        osm_id=1,
        distance=5000,
    )

    second = create_candidate(
        osm_id=2,
        distance=1000,
    )

    third = create_candidate(
        osm_id=3,
        distance=2500,
    )

    result = sort_candidates(
        [first, second, third],
        SortBy.DISTANCE,
    )

    assert result == [
        second,
        third,
        first,
    ]


def test_sort_missing_values_last():
    """Place candidates with missing travel values last."""

    first = create_candidate(
        osm_id=1,
        duration=None,
    )

    second = create_candidate(
        osm_id=2,
        duration=600,
    )

    third = create_candidate(
        osm_id=3,
        duration=300,
    )

    result = sort_candidates(
        [first, second, third],
        SortBy.DURATION,
    )

    assert result == [
        third,
        second,
        first,
    ]