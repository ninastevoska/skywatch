from typing import Any

from shared.constants import TransportMode
from shared.errors import RoutingError
from shared.models.location import Coordinates, CandidateLocation
from shared.models.requests import RouteRequest
from shared.models.responses import RouteResponse
from worker.clients.openrouteservice import OpenRouteServiceClient


MATRIX_BATCH_SIZE = 50


class RoutingService:
    def __init__(self, client: OpenRouteServiceClient):
        self.client = client

    async def enrich_candidates(
        self,
        origin: Coordinates,
        candidates: list[CandidateLocation],
        transport_mode: TransportMode,
    ) -> list[CandidateLocation]:
        """Enrich candidates with travel distances and durations."""

        enriched_candidates = []

        for start in range(0, len(candidates), MATRIX_BATCH_SIZE):
            batch = candidates[start:start + MATRIX_BATCH_SIZE]

            destinations = [
                candidate.coordinates
                for candidate in batch
            ]

            response = await self.client.get_matrix(
                origin,
                destinations,
                transport_mode,
            )

            enriched_candidates.extend(
                self._apply_matrix_response(batch, response)
            )

        return enriched_candidates

    @staticmethod
    def _apply_matrix_response(
        candidates: list[CandidateLocation],
        response: dict[str, Any],
    ) -> list[CandidateLocation]:
        """Apply matrix results to the corresponding candidates."""

        try:
            distances = response["distances"][0]
            durations = response["durations"][0]
            destinations = response["destinations"]

        except (KeyError, IndexError, TypeError) as exc:
            raise RoutingError(
                "Invalid matrix response."
            ) from exc

        if not (
            len(candidates)
            == len(distances)
            == len(durations)
            == len(destinations)
        ):
            raise RoutingError(
                "Matrix response does not match the candidates."
            )

        enriched_candidates = []

        for index, candidate in enumerate(candidates):
            enriched = candidate.model_copy(deep=True)

            enriched.travel_distance_m = distances[index]
            enriched.travel_duration_seconds = durations[index]

            destination = destinations[index]

            if destination is not None:
                enriched.snapped_distance_m = destination.get(
                    "snapped_distance"
                )

                location = destination.get("location")

                if location is not None:
                    longitude, latitude = location

                    enriched.snapped_coordinates = Coordinates(
                        latitude=latitude,
                        longitude=longitude,
                    )

            enriched_candidates.append(enriched)

        return enriched_candidates

    async def get_route(
        self,
        request: RouteRequest,
    ) -> RouteResponse:
        """Retrieve detailed navigation information."""

        response = await self.client.get_directions(
            request.origin,
            request.destination,
            request.transport_mode,
        )

        try:
            feature = response["features"][0]
            summary = feature["properties"]["summary"]
            geometry = feature["geometry"]

            return RouteResponse(
                origin=request.origin,
                destination=request.destination,
                transport_mode=request.transport_mode,
                distance_m=summary["distance"],
                duration_seconds=summary["duration"],
                geometry=geometry,
            )

        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise RoutingError(
                "Invalid directions response."
            ) from exc