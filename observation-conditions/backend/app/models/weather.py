from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class HourlyWeather:
    time: datetime
    cloud_cover: float
    precipitation_probability: float
    precipitation: float
    wind_speed: float

    @classmethod
    def from_dict(cls, data: dict) -> "HourlyWeather":
        """Create an hourly weather record from API data."""
        return cls(
            time=datetime.fromisoformat(data["time"]),
            cloud_cover=float(data["cloud_cover"]),
            precipitation_probability=float(
                data["precipitation_probability"]
            ),
            precipitation=float(data["precipitation"]),
            wind_speed=float(data["wind_speed"]),
        )
