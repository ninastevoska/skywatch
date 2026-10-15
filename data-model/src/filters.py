from datetime import date

from .models import Event
from .data_service import LinkedObservation


def filter_events(
    events: list[Event],
    event_type: str | None = None,
    date_from: date | None = None,
) -> list[Event]:
    results = []

    for event in events:
        if event_type is not None and event.type != event_type:
            continue

        if date_from is not None:
            if date.fromisoformat(event.date) < date_from:
                continue

        results.append(event)

    return results


def filter_observations(
    observations: list[LinkedObservation],
    event_type: str | None = None,
    date_from: date | None = None,
    max_cloud_cover: int | None = None,
) -> list[LinkedObservation]:
    results = []

    for record in observations:
        if event_type is not None and record.event.type != event_type:
            continue

        if date_from is not None:
            if date.fromisoformat(record.observation.date) < date_from:
                continue

        if max_cloud_cover is not None:
            weather = record.observation.weather

            if weather is None or weather.cloud_cover > max_cloud_cover:
                continue

        results.append(record)

    return results
