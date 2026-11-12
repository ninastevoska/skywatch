import os
from datetime import date, timedelta


GRPC_HOST = os.getenv("GRPC_HOST", "127.0.0.1")
GRPC_PORT = int(os.getenv("GRPC_PORT", "50051"))

OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
OPEN_METEO_GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"

FORECAST_DAYS = 15
REQUEST_TIMEOUT = 15.0


def get_forecast_date_range() -> tuple[date, date]:
    today = date.today()
    last_day = today + timedelta(days=FORECAST_DAYS - 1)

    return today, last_day


def is_valid_forecast_date(selected_date: date) -> bool:
    first_day, last_day = get_forecast_date_range()
    return first_day <= selected_date <= last_day
