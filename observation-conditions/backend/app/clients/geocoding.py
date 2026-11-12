import httpx

from app.config import OPEN_METEO_GEOCODING_URL, REQUEST_TIMEOUT


async def search_locations(query: str, count: int = 5) -> list[dict]:
    """Search for geographic locations by name."""
    query = query.strip()

    if len(query) < 2:
        raise ValueError("Location name must contain at least 2 characters.")

    if not 1 <= count <= 100:
        raise ValueError("Result count must be between 1 and 100.")

    params = {
        "name": query,
        "count": count,
        "language": "en",
        "format": "json",
    }

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        response = await client.get(
            OPEN_METEO_GEOCODING_URL,
            params=params,
        )
        response.raise_for_status()
        data = response.json()

    return [
        {
            "name": location["name"],
            "latitude": location["latitude"],
            "longitude": location["longitude"],
            "country": location.get("country"),
            "region": location.get("admin1"),
            "timezone": location.get("timezone"),
        }
        for location in data.get("results", [])
    ]
