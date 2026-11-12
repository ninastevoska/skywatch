from datetime import datetime, timedelta, timezone

from app.models.weather import HourlyWeather
from app.services.observation_windows import find_best_observation_windows


def make_forecast(cloud_covers: list[float]) -> list[HourlyWeather]:
    start = datetime(2026, 11, 12, 20, tzinfo=timezone.utc)

    return [
        HourlyWeather(
            time=start + timedelta(hours=index),
            cloud_cover=cloud_cover,
            precipitation_probability=0,
            precipitation=0,
            wind_speed=0,
        )
        for index, cloud_cover in enumerate(cloud_covers)
    ]


def test_consecutive_good_hours():
    windows = find_best_observation_windows(
        make_forecast([80, 20, 10, 15, 90])
    )

    assert len(windows) == 1
    assert windows[0].start_time.hour == 21
    assert windows[0].end_time.hour == 0
    assert windows[0].average_score == 91.0
    assert windows[0].is_recommended is True


def test_single_good_hour():
    windows = find_best_observation_windows(
        make_forecast([100, 90, 10, 95])
    )

    assert len(windows) == 1
    assert windows[0].start_time.hour == 22
    assert windows[0].end_time.hour == 23
    assert windows[0].is_recommended is True


def test_fallback_when_no_good_hours():
    windows = find_best_observation_windows(
        make_forecast([100, 90, 85, 95])
    )

    assert len(windows) == 1
    assert windows[0].average_score == 49.0
    assert windows[0].rating == "Fair"
    assert windows[0].is_recommended is False


def test_window_crosses_midnight():
    windows = find_best_observation_windows(
        make_forecast([90, 20, 10, 15, 90])
    )

    assert len(windows) == 1
    assert windows[0].start_time == datetime(
        2026, 11, 12, 21, tzinfo=timezone.utc
    )
    assert windows[0].end_time == datetime(
        2026, 11, 13, 0, tzinfo=timezone.utc
    )


def test_empty_forecast():
    assert find_best_observation_windows([]) == []
