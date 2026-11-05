from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AstronomicalEvent(BaseModel):
    """Astronomical event used by the SkyWatch AI module."""

    model_config = ConfigDict(extra="ignore")

    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    kind: str = Field(min_length=1)
    time: datetime
    description: str | None = None
    circumstances: dict[str, Any] = Field(default_factory=dict)
