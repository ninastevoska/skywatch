from math import sqrt
from typing import Any

from pyproj import Geod, Transformer
from shapely.geometry import (
    Polygon,
    MultiPolygon,
    GeometryCollection,
    Point,
    box,
    shape,
    mapping,
)
from shapely import transform
from shapely.ops import unary_union
from shapely.validation import make_valid

from shared.errors import GeometryError
from shared.models.location import Coordinates


# Coordinate transformations between WGS84 and Web Mercator.
TO_METRIC = Transformer.from_crs(
    "EPSG:4326",
    "EPSG:3857",
    always_xy=True,
)

TO_GEOGRAPHIC = Transformer.from_crs(
    "EPSG:3857",
    "EPSG:4326",
    always_xy=True,
)

GEOD = Geod(ellps="WGS84")


def extract_polygons(geometry) -> list[Polygon]:
    """Extract polygon components from a Shapely geometry."""

    if geometry.is_empty:
        return []

    if isinstance(geometry, Polygon):
        return [geometry]

    if isinstance(
        geometry,
        (MultiPolygon, GeometryCollection),
    ):
        polygons = []

        for component in geometry.geoms:
            polygons.extend(extract_polygons(component))

        return polygons

    return []


def extract_isochrone(
    response: dict[str, Any],
) -> Polygon | MultiPolygon:
    """Extract and merge polygons from an isochrone response."""

    polygons = []

    for feature in response.get("features", []):
        geometry = feature.get("geometry")

        if not geometry:
            continue

        try:
            polygon = shape(geometry)

            if not polygon.is_valid:
                polygon = make_valid(polygon)

            polygons.extend(extract_polygons(polygon))

        except (ValueError, TypeError, KeyError) as exc:
            raise GeometryError(
                "Invalid isochrone geometry."
            ) from exc

    if not polygons:
        raise GeometryError(
            "No valid isochrone polygons were returned."
        )

    return unary_union(polygons)


def projected_area_km2(
    geometry: Polygon | MultiPolygon,
) -> float:
    """Calculate the projected area in square kilometers."""

    projected = transform(
        geometry,
        TO_METRIC.transform,
        interleaved=False,
    )

    return projected.area / 1_000_000


def split_search_area(
    geometry: Polygon | MultiPolygon,
    max_area_km2: float,
) -> list[Polygon]:
    """Split an area into polygons suitable for POI requests."""

    if max_area_km2 <= 0:
        raise ValueError("Maximum area must be positive.")

    if geometry.is_empty:
        return []

    # Leave a small margin below the API area limit.
    max_area_m2 = max_area_km2 * 1_000_000 * 0.95

    projected = transform(
        geometry,
        TO_METRIC.transform,
        interleaved=False,
    )

    search_areas = []

    for polygon in extract_polygons(projected):
        if polygon.area <= max_area_m2:
            search_areas.append(polygon)
            continue

        cell_size = sqrt(max_area_m2)

        min_x, min_y, max_x, max_y = polygon.bounds

        x = min_x

        while x < max_x:
            y = min_y

            while y < max_y:
                cell = box(
                    x,
                    y,
                    x + cell_size,
                    y + cell_size,
                )

                intersection = polygon.intersection(cell)

                for part in extract_polygons(intersection):
                    if part.area > 0:
                        search_areas.append(part)

                y += cell_size

            x += cell_size

    return [
        transform(
            area,
            TO_GEOGRAPHIC.transform,
            interleaved=False,
        )
        for area in search_areas
    ]


def contains_coordinates(
    geometry: Polygon | MultiPolygon,
    coordinates: Coordinates,
) -> bool:
    """Check whether coordinates lie inside or on the boundary."""

    point = Point(
        coordinates.longitude,
        coordinates.latitude,
    )

    return geometry.covers(point)


def straight_line_distance_m(
    origin: Coordinates,
    destination: Coordinates,
) -> float:
    """Calculate the geodesic distance between two coordinates."""

    _, _, distance = GEOD.inv(
        origin.longitude,
        origin.latitude,
        destination.longitude,
        destination.latitude,
    )

    return float(distance)


def to_geojson(
    geometry: Polygon | MultiPolygon,
) -> dict[str, Any]:
    """Convert a Shapely geometry into GeoJSON."""

    return dict(mapping(geometry))