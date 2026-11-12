from dataclasses import dataclass

from app.models.weather import HourlyWeather


@dataclass(frozen=True)
class ConditionsResult:
    score: float
    rating: str
    reasons: list[str]


def get_rating(score: float) -> str:
    """Return a rating based on the observation conditions score."""
    if score >= 80:
        return "Excellent"
    if score >= 60:
        return "Good"
    if score >= 40:
        return "Fair"
    if score >= 20:
        return "Poor"
    return "Very poor"


def evaluate_conditions(weather: HourlyWeather) -> ConditionsResult:
    """Evaluate weather suitability for astronomical observation."""
    cloud_score = 100 - weather.cloud_cover
    rain_score = 100 - weather.precipitation_probability
    wind_score = max(0.0, 100 - weather.wind_speed * 5)

    score = (
        cloud_score * 0.60
        + rain_score * 0.25
        + wind_score * 0.15
    )

    if weather.precipitation > 0:
        score *= 0.5

    score = round(max(0.0, min(100.0, score)), 1)

    reasons = []

    if weather.cloud_cover >= 70:
        reasons.append("High cloud cover may obstruct the night sky.")
    elif weather.cloud_cover <= 20:
        reasons.append("Low cloud cover provides good sky visibility.")

    if weather.precipitation > 0:
        reasons.append("Precipitation is forecast during this period.")
    elif weather.precipitation_probability >= 60:
        reasons.append("There is a high probability of precipitation.")

    if weather.wind_speed >= 20:
        reasons.append("Strong wind may affect observation equipment.")
    elif weather.wind_speed <= 5:
        reasons.append("Low wind speed is favorable for observation.")

    if not reasons:
        reasons.append("Weather conditions are moderately favorable.")

    return ConditionsResult(
        score=score,
        rating=get_rating(score),
        reasons=reasons,
    )
