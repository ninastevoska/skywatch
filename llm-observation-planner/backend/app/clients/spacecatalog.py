from datetime import date, timedelta

import httpx
from pydantic import ValidationError

from app.config import get_settings
from app.models.event import AstronomicalEvent


class SpaceCatalogError(Exception):
    """Error raised when SpaceCatalog data cannot be retrieved."""


class SpaceCatalogClient:
    """Client for retrieving astronomical events from SpaceCatalog."""

    def __init__(self) -> None:
        settings = get_settings()

        self.base_url = settings.spacecatalog_base_url.rstrip("/")
        self.timeout = 20.0

    def get_events(
        self,
        from_date: date,
        to_date: date,
    ) -> list[AstronomicalEvent]:
        """Retrieve and validate astronomical events in a date range."""

        if from_date > to_date:
            raise ValueError(
                "The start date must not be after the end date."
            )

        if (to_date - from_date).days > 365:
            raise ValueError(
                "The selected date range cannot exceed 365 days."
            )

        params = {
            "from": from_date.isoformat(),
            "to": (to_date + timedelta(days=1)).isoformat(),
            "limit": 500,
        }

        try:
            response = httpx.get(
                f"{self.base_url}/events",
                params=params,
                timeout=self.timeout,
            )

            response.raise_for_status()
            data = response.json()

        except httpx.HTTPError as exc:
            raise SpaceCatalogError(
                "Failed to retrieve events from SpaceCatalog."
            ) from exc

        except ValueError as exc:
            raise SpaceCatalogError(
                "SpaceCatalog returned invalid JSON."
            ) from exc

        if not isinstance(data, dict):
            raise SpaceCatalogError(
                "Unexpected SpaceCatalog response format."
            )

        raw_events = data.get("events")

        if not isinstance(raw_events, list):
            raise SpaceCatalogError(
                "SpaceCatalog response does not contain an events list."
            )

        try:
            events = [
                AstronomicalEvent.model_validate(event)
                for event in raw_events
            ]

        except ValidationError as exc:
            raise SpaceCatalogError(
                "SpaceCatalog returned invalid event data."
            ) from exc

        return events
