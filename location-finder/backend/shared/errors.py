class SkyWatchError(Exception):
    """Base exception for the Location Finder application."""

    code = "INTERNAL_ERROR"

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


# Named pipe errors
class PipeError(SkyWatchError):
    code = "PIPE_ERROR"


class PipeConnectionError(PipeError):
    code = "PIPE_CONNECTION_ERROR"


class PipeTimeoutError(PipeError):
    code = "PIPE_TIMEOUT"


class PipeProtocolError(PipeError):
    code = "PIPE_PROTOCOL_ERROR"


# External API errors
class ExternalAPIError(SkyWatchError):
    code = "EXTERNAL_API_ERROR"

    def __init__(
        self,
        service: str,
        message: str,
        status_code: int | None = None,
    ):
        super().__init__(f"{service}: {message}")
        self.service = service
        self.status_code = status_code


# Location discovery errors
class DiscoveryError(SkyWatchError):
    code = "DISCOVERY_ERROR"


class GeometryError(DiscoveryError):
    code = "GEOMETRY_ERROR"


class RoutingError(SkyWatchError):
    code = "ROUTING_ERROR"