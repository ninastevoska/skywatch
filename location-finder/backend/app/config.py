from pydantic import Field

from shared.config import SharedSettings


class AppSettings(SharedSettings):
    app_host: str = "127.0.0.1"
    app_port: int = Field(default=8003, ge=1, le=65535)

    geocoding_base_url: str = (
        "https://geocoding-api.open-meteo.com/v1"
    )

    http_timeout: float = Field(default=15.0, gt=0)


settings = AppSettings()