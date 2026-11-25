import httpx

from app.config import settings
from shared.errors import ExternalAPIError
from shared.models.location import Coordinates, Location


class GeocodingClient:
    SERVICE_NAME = "Open-Meteo Geocoding"

    def __init__(self):
        self.base_url = settings.geocoding_base_url
        self.timeout = settings.http_timeout

    async def search(
        self,
        name: str,
        limit: int = 10,
    ) -> list[Location]:
        """Search for geographic locations by name."""

        params = {
            "name": name,
            "count": limit,
            "language": "en",
            "format": "json",
        }

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout
            ) as client:
                response = await client.get(
                    f"{self.base_url}/search",
                    params=params,
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

        return self._parse_locations(data)

    @staticmethod
    def _parse_locations(data: dict) -> list[Location]:
        """Convert API results into shared location models."""

        locations = []

        for result in data.get("results", []):
            location = Location(
                coordinates=Coordinates(
                    latitude=result["latitude"],
                    longitude=result["longitude"],
                ),
                name=result.get("name"),
                country=result.get("country"),
                region=result.get("admin1"),
                timezone=result.get("timezone"),
            )

            locations.append(location)

        return locations