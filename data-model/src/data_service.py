from dataclasses import dataclass

from .models import Event, Location, Observation


@dataclass
class LinkedObservation:
    observation: Observation
    event: Event
    location: Location


def link_data(
    events: list[Event],
    locations: list[Location],
    observations: list[Observation],
) -> list[LinkedObservation]:

    events_by_id = {event.id: event for event in events}
    locations_by_id = {location.id: location for location in locations}

    linked_observations = []

    for observation in observations:
        event = events_by_id.get(observation.event_id)
        location = locations_by_id.get(observation.location_id)

        if event is None or location is None:
            raise ValueError(
                f"Observation {observation.id} contains an invalid "
                f"reference: event={observation.event_id}, "
                f"location={observation.location_id}"
            )

        linked = LinkedObservation(
            observation=observation,
            event=event,
            location=location,
        )

        linked_observations.append(linked)

    return linked_observations
