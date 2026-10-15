import xml.etree.ElementTree as ET
from pathlib import Path

from .models import Event, Location, Observation, Weather


def read_events(path: Path) -> list[Event]:
    tree = ET.parse(path)
    root = tree.getroot()

    events = []

    for element in root.findall("event"):
        event = Event(
            id=element.attrib["id"],
            api_id=element.findtext("api_id"),
            name=element.findtext("name"),
            type=element.findtext("type"),
            date=element.findtext("date"),
            time=element.findtext("time"),
            description=element.findtext("description"),
            right_ascension=float(element.findtext("right_ascension")),
            declination=float(element.findtext("declination")),
            objects=[
                obj.text
                for obj in element.findall("objects/object")
                if obj.text
            ],
            window_start=element.findtext("window_start"),
            window_end=element.findtext("window_end"),
        )

        events.append(event)

    return events


def read_locations(path: Path) -> list[Location]:
    tree = ET.parse(path)
    root = tree.getroot()

    locations = []

    for element in root.findall("location"):
        location = Location(
            id=element.attrib["id"],
            osm_id=element.findtext("osm_id"),
            osm_type=element.findtext("osm_type"),
            name=element.findtext("name"),
            category=element.findtext("category"),
            latitude=float(element.findtext("latitude")),
            longitude=float(element.findtext("longitude")),
        )

        locations.append(location)

    return locations


def read_observations(path: Path) -> list[Observation]:
    tree = ET.parse(path)
    root = tree.getroot()

    observations = []

    for element in root.findall("observation"):
        weather_element = element.find("weather")
        weather = None

        if weather_element is not None:
            visibility = weather_element.findtext("visibility")

            weather = Weather(
                source=weather_element.findtext("source"),
                weather_timestamp=weather_element.findtext(
                    "weather_timestamp"
                ),
                cloud_cover=int(weather_element.findtext("cloud_cover")),
                precipitation=float(weather_element.findtext("precipitation")),
                wind_speed=float(
                    weather_element.findtext("wind_speed")
                ),
                weather_latitude=float(
                    weather_element.findtext("weather_latitude")
                ),
                weather_longitude=float(
                    weather_element.findtext("weather_longitude")
                ),
                visibility=(
                    float(visibility)
                    if visibility is not None and visibility.strip()
                    else None
                ),
            )

        observation = Observation(
            id=element.attrib["id"],
            event_id=element.findtext("event_id"),
            location_id=element.findtext("location_id"),
            date=element.findtext("date"),
            time=element.findtext("time"),
            timezone=element.findtext("timezone"),
            data_type=element.findtext("data_type"),
            weather=weather,
        )

        observations.append(observation)

    return observations
