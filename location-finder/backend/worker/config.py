from pydantic import Field, SecretStr

from shared.config import SharedSettings


class WorkerSettings(SharedSettings):
    ors_api_key: SecretStr

    ors_base_url: str = (
        "https://api.heigit.org/openrouteservice/v2"
    )

    ops_base_url: str = (
        "https://api.heigit.org/openpoiservice/v0"
    )

    http_timeout: float = Field(default=15.0, gt=0)

    poi_max_area_km2: float = Field(
        default=50.0,
        gt=0,
        le=50,
    )

    poi_max_requests: int = Field(default=30, gt=0)

    poi_max_candidates: int = Field(default=500, gt=0)


settings = WorkerSettings()