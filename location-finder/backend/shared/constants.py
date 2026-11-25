from enum import StrEnum


# Named pipe protocol
PROTOCOL_VERSION = "1.0"
MESSAGE_HEADER_SIZE = 4


class PipeOperation(StrEnum):
    PING = "ping"
    FIND_LOCATIONS = "find_locations"
    GET_ROUTE = "get_route"


class ResponseStatus(StrEnum):
    SUCCESS = "success"
    ERROR = "error"


# Supported transport profiles
class TransportMode(StrEnum):
    CAR = "driving-car"
    BICYCLE = "cycling-regular"
    WALKING = "foot-walking"


class RangeType(StrEnum):
    TIME = "time"
    DISTANCE = "distance"


class SortBy(StrEnum):
    DURATION = "duration"
    DISTANCE = "distance"


# Observation location categories
class LocationCategory(StrEnum):
    VIEWPOINT = "viewpoint"
    PEAK = "peak"
    SADDLE = "saddle"
    PARK = "park"
    CAMP_SITE = "camp_site"


CATEGORY_IDS: dict[LocationCategory, int] = {
    LocationCategory.VIEWPOINT: 627,
    LocationCategory.PEAK: 335,
    LocationCategory.SADDLE: 337,
    LocationCategory.PARK: 280,
    LocationCategory.CAMP_SITE: 103,
}

DEFAULT_CATEGORIES = (
    LocationCategory.VIEWPOINT,
    LocationCategory.PEAK,
    LocationCategory.SADDLE,
)


# Isochrones limits in seconds and meters
MAX_TIME_SECONDS = {
    TransportMode.CAR: 3600,
    TransportMode.BICYCLE: 18000,
    TransportMode.WALKING: 72000,
}

MAX_DISTANCE_METERS = 120000


# POI API limits
MAX_POI_CATEGORIES = 5
MAX_POI_BUFFER_METERS = 2000


# Application defaults
DEFAULT_RANGE_SECONDS = 1800
DEFAULT_RANGE_METERS = 10000

DEFAULT_RESULTS = 10
MAX_RESULTS = 50