from dataclasses import dataclass
from datetime import datetime, timedelta

from app.models.weather import HourlyWeather
from app.services.conditions import evaluate_conditions, get_rating


MIN_SCORE = 60
MIN_DURATION_HOURS = 1
MAX_WINDOWS = 3


@dataclass(frozen=True)
class ObservationWindow:
    start_time: datetime
    end_time: datetime
    average_score: float
    rating: str
    is_recommended: bool


def find_best_observation_windows(
    forecast: list[HourlyWeather],
) -> list[ObservationWindow]:
    """Find recommended observation windows or the best fallback hour."""
    if not forecast:
        return []

    sorted_forecast = sorted(forecast, key=lambda item: item.time)
    windows = []
    current_hours = []

    def save_window() -> None:
        if len(current_hours) < MIN_DURATION_HOURS:
            return

        scores = [
            evaluate_conditions(weather).score
            for weather in current_hours
        ]
        average_score = round(sum(scores) / len(scores), 1)

        windows.append(
            ObservationWindow(
                start_time=current_hours[0].time,
                end_time=current_hours[-1].time + timedelta(hours=1),
                average_score=average_score,
                rating=get_rating(average_score),
                is_recommended=True,
            )
        )

    for weather in sorted_forecast:
        score = evaluate_conditions(weather).score

        if score < MIN_SCORE:
            save_window()
            current_hours = []
            continue

        if current_hours:
            expected_time = current_hours[-1].time + timedelta(hours=1)

            if weather.time != expected_time:
                save_window()
                current_hours = []

        current_hours.append(weather)

    save_window()

    if windows:
        windows.sort(
            key=lambda window: (
                -window.average_score,
                window.start_time,
            )
        )
        return windows[:MAX_WINDOWS]

    best_hour = max(
        sorted_forecast,
        key=lambda weather: evaluate_conditions(weather).score,
    )
    best_score = evaluate_conditions(best_hour).score

    return [
        ObservationWindow(
            start_time=best_hour.time,
            end_time=best_hour.time + timedelta(hours=1),
            average_score=best_score,
            rating=get_rating(best_score),
            is_recommended=False,
        )
    ]
