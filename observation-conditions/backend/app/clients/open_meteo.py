import math
from datetime import date

import httpx

from app.config import (
    OPEN_METEO_FORECAST_URL,
    REQUEST_TIMEOUT,
    is_valid_forecast_date,
)


HOURLY_VARIABLES = [
    "cloud_cover",
    "precipitation_probability",
    "precipitation",
    "wind_speed_10m",
]


async def get_weather_forecast(
    latitude: float,
    longitude: float,
    start_date: date,
    end_date: date,
) -> list[dict]:
    """Fetch hourly weather forecasts for a location and date range."""
    if not math.isfinite(latitude) or not -90 <= latitude <= 90:
        raise ValueError("Latitude must be between -90 and 90.")

    if not math.isfinite(longitude) or not -180 <= longitude <= 180:
        raise ValueError("Longitude must be between -180 and 180.")

    if start_date > end_date:
        raise ValueError("Start date must not be after end date.")

    if not (
        is_valid_forecast_date(start_date)
        and is_valid_forecast_date(end_date)
    ):
        raise ValueError("Dates must be within the forecast period.")

   
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": ",".join(HOURLY_VARIABLES),
        "forecast_days": 16,
        "timezone": "GMT",
        "wind_speed_unit": "kmh",
        "precipitation_unit": "mm",
    }


    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        response = await client.get(
            OPEN_METEO_FORECAST_URL,
            params=params,
        )
        response.raise_for_status()
        data = response.json()

    hourly = data["hourly"]
    times = hourly["time"]
    variables = {name: hourly[name] for name in HOURLY_VARIABLES}

    if any(len(values) != len(times) for values in variables.values()):
        raise ValueError("Incomplete weather forecast response.")

    forecast = []

    
    for index, time in enumerate(times):
        forecast_date = date.fromisoformat(time[:10])

        if not start_date <= forecast_date <= end_date:
            continue

        values = {name: items[index] for name, items in variables.items()}


        if any(value is None for value in values.values()):
            continue

        forecast.append({
            "time": f"{time}:00+00:00",
            "cloud_cover": values["cloud_cover"],
            "precipitation_probability": values["precipitation_probability"],
            "precipitation": values["precipitation"],
            "wind_speed": values["wind_speed_10m"],
        })

    if not forecast:
        raise ValueError("No weather forecast is available for this period.")

    return forecast
