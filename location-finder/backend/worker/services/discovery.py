from shapely.geometry import Point

from shared.models.requests import DiscoveryRequest
from shared.models.responses import DiscoveryResponse
from worker.config import settings
from worker.clients.openrouteservice import OpenRouteServiceClient
from worker.clients.openpoiservice import OpenPoiServiceClient
from worker.services.routing import RoutingService
from worker.services.geometry import (
    extract_isochrone,
    split_search_area,
    to_geojson,
)
from worker.services.candidates import (
    parse_candidates,
    deduplicate_candidates,
    filter_by_geometry,
    filter_by_range,
    sort_candidates,
)


class DiscoveryService:
    def __init__(
        self,
        ors_client: OpenRouteServiceClient,
        ops_client: OpenPoiServiceClient,
        routing_service: RoutingService,
    ):
        self.ors_client = ors_client
        self.ops_client = ops_client
        self.routing_service = routing_service

    async def discover(
        self,
        request: DiscoveryRequest,
    ) -> DiscoveryResponse:
        """Discover reachable observation locations."""

        warnings = []
        origin = request.origin.coordinates

        # 1. Retrieve the reachable area.
        isochrone_response = await self.ors_client.get_isochrones(
            origin=origin,
            transport_mode=request.transport_mode,
            range_type=request.range_type,
            range_value=request.range_value,
        )

        isochrone = extract_isochrone(isochrone_response)

        # 2. Split the area into smaller POI search polygons.
        search_areas = split_search_area(
            isochrone,
            settings.poi_max_area_km2,
        )

        # Prioritize search areas closer to the origin.
        origin_point = Point(
            origin.longitude,
            origin.latitude,
        )

        search_areas.sort(
            key=lambda area: area.distance(origin_point)
        )

        if len(search_areas) > settings.poi_max_requests:
            warnings.append(
                "The search area was only partially processed "
                "due to the POI request limit."
            )

            search_areas = search_areas[
                :settings.poi_max_requests
            ]

        # 3. Retrieve POIs from each search area.
        candidates = []
        poi_limit_reached = False

        for area in search_areas:
            response = await self.ops_client.get_pois(
                geometry=to_geojson(area),
                categories=request.categories,
                buffer_m=0,
                limit=settings.poi_max_candidates,
            )

            if (
                len(response["features"])
                >= settings.poi_max_candidates
            ):
                poi_limit_reached = True

            candidates.extend(
                parse_candidates(response, origin)
            )

        if poi_limit_reached:
            warnings.append(
                "Some search areas may contain additional "
                "locations beyond the POI response limit."
            )

        # 4. Normalize and filter candidates.
        candidates = deduplicate_candidates(candidates)

        candidates = filter_by_geometry(
            candidates,
            isochrone,
        )

        # Limit the number of candidates sent to the Matrix API.
        if len(candidates) > settings.poi_max_candidates:
            candidates.sort(
                key=lambda candidate: (
                    candidate.straight_line_distance_m
                    if candidate.straight_line_distance_m is not None
                    else float("inf")
                )
            )

            candidates = candidates[
                :settings.poi_max_candidates
            ]

            warnings.append(
                "Only the geographically closest candidates "
                "were evaluated due to the candidate limit."
            )

        # 5. Retrieve travel distances and durations.
        candidates = await self.routing_service.enrich_candidates(
            origin=origin,
            candidates=candidates,
            transport_mode=request.transport_mode,
        )

        # 6. Filter by travel range and sort the results.
        candidates = filter_by_range(
            candidates,
            request,
        )

        candidates = sort_candidates(
            candidates,
            request.sort_by,
        )

        total_candidates = len(candidates)

        # 7. Apply the requested result limit.
        candidates = candidates[:request.max_results]

        return DiscoveryResponse(
            origin=request.origin,
            transport_mode=request.transport_mode,
            range_type=request.range_type,
            range_value=request.range_value,
            isochrone=to_geojson(isochrone),
            candidates=candidates,
            total_candidates=total_candidates,
            warnings=warnings,
        )