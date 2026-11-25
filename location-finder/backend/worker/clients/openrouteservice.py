from typing import Any

import httpx

from shared.constants import RangeType, TransportMode
from shared.errors import ExternalAPIError
from shared.models.location import Coordinates
from worker.config import settings


class OpenRouteServiceClient:
    SERVICE_NAME = "OpenRouteService"

    def __init__(self):
        self.base_url = settings.ors_base_url.rstrip("/")
        self.timeout = settings.http_timeout

        self.headers = {
            "Authorization": settings.ors_api_key.get_secret_value(),
            "Content-Type": "application/json",
            "Accept": "application/json, application/geo+json",
        }

    async def get_isochrones(
        self,
        origin: Coordinates,
        transport_mode: TransportMode,
        range_type: RangeType,
        range_value: int,
    ) -> dict[str, Any]:
        """Retrieve the area reachable within the given range."""

        payload = {
            "locations": [origin.to_geojson()],
            "range": [range_value],
            "range_type": range_type.value,
        }

        return await self._post(
            f"/isochrones/{transport_mode.value}",
            payload,
        )

    async def get_matrix(
        self,
        origin: Coordinates,
        destinations: list[Coordinates],
        transport_mode: TransportMode,
    ) -> dict[str, Any]:
        """Retrieve travel distances and durations to destinations."""

        if not destinations:
            raise ValueError("At least one destination is required.")

        locations = [origin.to_geojson()]
        locations.extend(
            destination.to_geojson()
            for destination in destinations
        )

        payload = {
            "locations": locations,
            "sources": [0],
            "destinations": list(range(1, len(locations))),
            "metrics": ["distance", "duration"],
            "units": "m",
        }

        return await self._post(
            f"/matrix/{transport_mode.value}",
            payload,
        )

    async def get_directions(
        self,
        origin: Coordinates,
        destination: Coordinates,
        transport_mode: TransportMode,
    ) -> dict[str, Any]:
        """Retrieve the route between two geographic locations."""

        payload = {
            "coordinates": [
                origin.to_geojson(),
                destination.to_geojson(),
            ],
        }

        return await self._post(
            f"/directions/{transport_mode.value}/geojson",
            payload,
        )

    async def _post(
        self,
        endpoint: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Send an authenticated POST request to OpenRouteService."""

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                headers=self.headers,
            ) as client:
                response = await client.post(
                    f"{self.base_url}{endpoint}",
                    json=payload,
                )

                response.raise_for_status()
                data = response.json()

        except httpx.TimeoutException as exc:
            raise ExternalAPIError(
                self.SERVICE_NAME,
                "Request timed out.",
            ) from exc

        except httpx.HTTPStatusError as exc:
            raise ExternalAPIError(
                self.SERVICE_NAME,
                (
                    f"Request to {endpoint} failed "
                    f"(HTTP {exc.response.status_code}): "
                    f"{exc.response.text}"
                ),
                status_code=exc.response.status_code,
            ) from exc

        except httpx.RequestError as exc:
            raise ExternalAPIError(
                self.SERVICE_NAME,
                "Unable to connect to the service.",
            ) from exc

        except ValueError as exc:
            raise ExternalAPIError(
                self.SERVICE_NAME,
                "Invalid JSON response.",
            ) from exc

        if not isinstance(data, dict):
            raise ExternalAPIError(
                self.SERVICE_NAME,
                "Unexpected response format.",
            )

        return data