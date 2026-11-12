from datetime import datetime, timezone

import pytest

from app.models.weather import HourlyWeather
from app.services.conditions import evaluate_conditions, get_rating


def make_weather(
    cloud_cover: float = 0,
    precipitation_probability: float = 0,
    precipitation: float = 0,
    wind_speed: float = 0,
) -> HourlyWeather:
    return HourlyWeather(
        time=datetime(2026, 11, 12, 21, 0, tzinfo=timezone.utc),
        cloud_cover=cloud_cover,
        precipitation_probability=precipitation_probability,
        precipitation=precipitation,
        wind_speed=wind_speed,
    )


def test_excellent_conditions():
    result = evaluate_conditions(make_weather())

    assert result.score == 100
    assert result.rating == "Excellent"


def test_poor_conditions():
    weather = make_weather(
        cloud_cover=100,
        precipitation_probability=100,
        wind_speed=25,
    )
    result = evaluate_conditions(weather)

    assert result.score == 0
    assert result.rating == "Very poor"


def test_precipitation_reduces_score():
    dry = evaluate_conditions(make_weather(cloud_cover=20))
    rainy = evaluate_conditions(
        make_weather(cloud_cover=20, precipitation=1.0)
    )

    assert rainy.score == pytest.approx(dry.score * 0.5)
    assert "Precipitation is forecast during this period." in rainy.reasons


def test_rating_boundaries():
    assert get_rating(0) == "Very poor"
    assert get_rating(20) == "Poor"
    assert get_rating(40) == "Fair"
    assert get_rating(60) == "Good"
    assert get_rating(80) == "Excellent"


def test_maribor_example():
    weather = make_weather(
        cloud_cover=100,
        precipitation_probability=0,
        precipitation=0,
        wind_speed=2.7,
    )
    result = evaluate_conditions(weather)

    assert result.score == 38.0
    assert result.rating == "Poor"
