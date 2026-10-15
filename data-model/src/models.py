from dataclasses import dataclass, field


@dataclass
class Event:
    id: str
    api_id: str
    name: str
    type: str
    date: str
    time: str
    description: str
    right_ascension: float
    declination: float
    objects: list[str] = field(default_factory=list)
    window_start: str | None = None
    window_end: str | None = None


@dataclass
class Location:
    id: str
    osm_id: str
    osm_type: str
    category: str
    latitude: float
    longitude: float
    name: str | None = None


@dataclass
class Weather:
    source: str
    weather_timestamp: str
    cloud_cover: int
    precipitation: float
    wind_speed: float
    weather_latitude: float
    weather_longitude: float
    visibility: float | None = None


@dataclass
class Observation:
    id: str
    event_id: str
    location_id: str
    date: str
    time: str
    timezone: str
    data_type: str
    weather: Weather | None = None
