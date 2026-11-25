from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"


class SharedSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    pipe_name: str = "skywatch_location_finder"

    pipe_connect_timeout: float = Field(default=15.0, gt=0)
    pipe_response_timeout: float = Field(default=120.0, gt=0)
    pipe_retry_interval: float = Field(default=0.5, gt=0)

    pipe_max_message_size: int = Field(
        default=10 * 1024 * 1024,
        gt=0,
    )

    @property
    def pipe_path(self) -> str:
        return rf"\\.\pipe\{self.pipe_name}"



shared_settings = SharedSettings()