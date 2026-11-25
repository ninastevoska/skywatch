from typing import Any

import httpx

from shared.constants import (
    CATEGORY_IDS,
    LocationCategory,
    MAX_POI_CATEGORIES,
    MAX_POI_BUFFER_METERS,
)
from shared.errors import ExternalAPIError
from worker.config import settings


class OpenPoiServiceClient:
    SERVICE_NAME = "OpenPoiService"

    def __init__(self):
        self.base_url = settings.ops_base_url.rstrip("/")
        self.timeout = settings.http_timeout

        self.headers = {
            "Authorization": settings.ors_api_key.get_secret_value(),
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def get_pois(
        self,
        geometry: dict[str, Any],
        categories: list[LocationCategory],
        buffer_m: int = 0,
        limit: int = 500,
    ) -> dict[str, Any]:
        """Retrieve points of interest within a geographic area."""

        if not 1 <= len(categories) <= MAX_POI_CATEGORIES:
            raise ValueError(
                f"Between 1 and {MAX_POI_CATEGORIES} "
                "categories are required."
            )

        if not 0 <= buffer_m <= MAX_POI_BUFFER_METERS:
            raise ValueError(
                f"Buffer must be between 0 and "
                f"{MAX_POI_BUFFER_METERS} meters."
            )

        if limit <= 0:
            raise ValueError("Limit must be positive.")

        category_ids = [
            CATEGORY_IDS[category]
            for category in categories
        ]

        payload = {
            "request": "pois",
            "geometry": {
                "geojson": geometry,
                "buffer": buffer_m,
            },
            "filters": {
                "category_ids": category_ids,
            },
            "limit": limit,
        }

        return await self._post(payload)

    async def _post(
        self,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Send an authenticated POST request to OpenPoiService."""

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                headers=self.headers,
            ) as client:
                response = await client.post(
                    f"{self.base_url}/pois",
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
                "Request failed.",
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

        if (
            not isinstance(data, dict)
            or data.get("type") != "FeatureCollection"
            or not isinstance(data.get("features"), list)
        ):
            raise ExternalAPIError(
                self.SERVICE_NAME,
                "Unexpected response format.",
            )

        return data