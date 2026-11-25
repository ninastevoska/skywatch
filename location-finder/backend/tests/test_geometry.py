import pytest

from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union

from shared.models.location import Coordinates

from worker.services.geometry import (
    extract_polygons,
    extract_isochrone,
    projected_area_km2,
    split_search_area,
    contains_coordinates,
    straight_line_distance_m,
    to_geojson,
)


@pytest.fixture
def small_polygon():
    """Create a small geographic area near Maribor."""

    return Polygon([
        (15.640, 46.550),
        (15.650, 46.550),
        (15.650, 46.560),
        (15.640, 46.560),
        (15.640, 46.550),
    ])


@pytest.fixture
def large_polygon():
    """Create an area exceeding the POI service area limit."""

    return Polygon([
        (15.40, 46.40),
        (15.70, 46.40),
        (15.70, 46.60),
        (15.40, 46.60),
        (15.40, 46.40),
    ])


def test_extract_single_polygon(small_polygon):
    """Extract a polygon from a simple geometry."""

    polygons = extract_polygons(small_polygon)

    assert len(polygons) == 1
    assert polygons[0].equals(small_polygon)


def test_extract_multipolygon(small_polygon):
    """Extract individual polygons from a MultiPolygon."""

    second_polygon = Polygon([
        (15.660, 46.550),
        (15.670, 46.550),
        (15.670, 46.560),
        (15.660, 46.560),
        (15.660, 46.550),
    ])

    geometry = MultiPolygon([
        small_polygon,
        second_polygon,
    ])

    polygons = extract_polygons(geometry)

    assert len(polygons) == 2
    assert unary_union(polygons).equals(geometry)


def test_extract_isochrone(small_polygon):
    """Extract an isochrone from a GeoJSON FeatureCollection."""

    response = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": to_geojson(small_polygon),
                "properties": {
                    "value": 1800,
                },
            },
        ],
    }

    geometry = extract_isochrone(response)

    assert geometry.is_valid
    assert geometry.equals(small_polygon)


def test_projected_area(small_polygon, large_polygon):
    """Verify projected geographic area calculation."""

    small_area = projected_area_km2(small_polygon)
    large_area = projected_area_km2(large_polygon)

    assert 0 < small_area < 50
    assert large_area > 50
    assert large_area > small_area


def test_small_area_does_not_require_splitting(small_polygon):
    """Keep areas that already satisfy the area limit."""

    parts = split_search_area(
        small_polygon,
        50,
    )

    assert len(parts) == 1
    assert parts[0].equals_exact(
        small_polygon,
        tolerance=1e-9,
    )


def test_large_area_splitting(large_polygon):
    """Ensure all resulting areas satisfy the POI limit."""

    parts = split_search_area(
        large_polygon,
        50,
    )

    assert len(parts) > 1

    for part in parts:
        assert part.is_valid
        assert not part.is_empty
        assert projected_area_km2(part) <= 50


def test_splitting_preserves_area(large_polygon):
    """Verify that splitting does not lose or duplicate area."""

    parts = split_search_area(
        large_polygon,
        50,
    )

    original_area = projected_area_km2(large_polygon)

    combined_area = sum(
        projected_area_km2(part)
        for part in parts
    )

    assert combined_area == pytest.approx(
        original_area,
        rel=1e-6,
    )

    combined_geometry = unary_union(parts)

    difference = large_polygon.symmetric_difference(
        combined_geometry
    )

    assert difference.area == pytest.approx(
        0,
        abs=1e-9,
    )


def test_coordinates_inside_polygon(small_polygon):
    """Accept coordinates inside the search area."""

    coordinates = Coordinates(
        latitude=46.555,
        longitude=15.645,
    )

    assert contains_coordinates(
        small_polygon,
        coordinates,
    )


def test_coordinates_outside_polygon(small_polygon):
    """Reject coordinates outside the search area."""

    coordinates = Coordinates(
        latitude=47.000,
        longitude=16.000,
    )

    assert not contains_coordinates(
        small_polygon,
        coordinates,
    )


def test_coordinates_on_polygon_boundary(small_polygon):
    """Include coordinates located on the area boundary."""

    coordinates = Coordinates(
        latitude=46.550,
        longitude=15.640,
    )

    assert contains_coordinates(
        small_polygon,
        coordinates,
    )


def test_zero_straight_line_distance():
    """Identical coordinates must have zero distance."""

    coordinates = Coordinates(
        latitude=46.5547,
        longitude=15.6459,
    )

    distance = straight_line_distance_m(
        coordinates,
        coordinates,
    )

    assert distance == pytest.approx(0)


def test_straight_line_distance():
    """Verify geographic distance and its symmetry."""

    first = Coordinates(
        latitude=46.55,
        longitude=15.65,
    )

    second = Coordinates(
        latitude=46.56,
        longitude=15.65,
    )

    forward_distance = straight_line_distance_m(
        first,
        second,
    )

    reverse_distance = straight_line_distance_m(
        second,
        first,
    )

    assert 1100 < forward_distance < 1120

    assert forward_distance == pytest.approx(
        reverse_distance
    )


def test_geojson_conversion(small_polygon):
    """Verify conversion into GeoJSON geometry."""

    geometry = to_geojson(small_polygon)

    assert geometry["type"] == "Polygon"

    first_coordinate = geometry["coordinates"][0][0]

    assert first_coordinate[0] == pytest.approx(15.640)
    assert first_coordinate[1] == pytest.approx(46.550)