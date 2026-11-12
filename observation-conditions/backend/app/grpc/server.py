import asyncio
import logging
from datetime import datetime, timedelta, timezone

import grpc
import httpx

from proto import observation_conditions_pb2 as pb2
from proto import observation_conditions_pb2_grpc as pb2_grpc

from app.clients.open_meteo import get_weather_forecast
from app.config import GRPC_HOST, GRPC_PORT
from app.models.weather import HourlyWeather
from app.services.conditions import evaluate_conditions
from app.services.observation_windows import find_best_observation_windows


logger = logging.getLogger(__name__)


def parse_time(value: str) -> datetime:
    """Parse an ISO 8601 timestamp and convert it to UTC."""
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("Invalid ISO 8601 timestamp.") from exc

    if parsed.tzinfo is None:
        raise ValueError("Timestamp must include a timezone.")

    parsed = parsed.astimezone(timezone.utc)

    if parsed.minute or parsed.second or parsed.microsecond:
        raise ValueError("Time must be aligned to a full hour.")

    return parsed


async def load_forecast(location, start_time: str, end_time: str):
    """Load weather data for a UTC time interval."""
    start = parse_time(start_time)
    end = parse_time(end_time)

    if start >= end:
        raise ValueError("Start time must be before end time.")

    # The end of an interval is exclusive.
    last_included_hour = end - timedelta(hours=1)

    data = await get_weather_forecast(
        latitude=location.latitude,
        longitude=location.longitude,
        start_date=start.date(),
        end_date=last_included_hour.date(),
    )

    forecast = [
        HourlyWeather.from_dict(item)
        for item in data
    ]

    return [
        weather
        for weather in forecast
        if start <= weather.time < end
    ]


def to_proto_weather(weather: HourlyWeather):
    return pb2.HourlyWeather(
        time=weather.time.isoformat(),
        cloud_cover=weather.cloud_cover,
        precipitation_probability=weather.precipitation_probability,
        precipitation=weather.precipitation,
        wind_speed=weather.wind_speed,
    )


class ObservationConditionsService(
    pb2_grpc.ObservationConditionsServiceServicer
):
    async def load_or_abort(self, context, location, start, end):
        try:
            forecast = await load_forecast(location, start, end)

            if not forecast:
                await context.abort(
                    grpc.StatusCode.NOT_FOUND,
                    "No weather data available for the selected period.",
                )

            return forecast

        except ValueError as exc:
            await context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                str(exc),
            )
        except (httpx.HTTPError, KeyError, TypeError) as exc:
            logger.warning("Weather API error: %s", exc)
            await context.abort(
                grpc.StatusCode.UNAVAILABLE,
                "Weather forecast service is unavailable.",
            )

    async def GetWeatherForecast(self, request, context):
        forecast = await self.load_or_abort(
            context,
            request.location,
            request.start_time,
            request.end_time,
        )

        return pb2.WeatherForecastResponse(
            location=request.location,
            hourly=[to_proto_weather(item) for item in forecast],
        )

    async def EvaluateConditions(self, request, context):
        selected_time = parse_time_or_none(request.time, context)
        selected_time = await selected_time

        forecast = await self.load_or_abort(
            context,
            request.location,
            selected_time.isoformat(),
            (selected_time + timedelta(hours=1)).isoformat(),
        )

        weather = forecast[0]
        result = evaluate_conditions(weather)

        return pb2.ConditionsResponse(
            location=request.location,
            time=weather.time.isoformat(),
            score=result.score,
            rating=result.rating,
            reasons=result.reasons,
            weather=to_proto_weather(weather),
        )

    async def FindBestObservationWindows(self, request, context):
        forecast = await self.load_or_abort(
            context,
            request.location,
            request.start_time,
            request.end_time,
        )

        windows = find_best_observation_windows(forecast)

        return pb2.ObservationWindowsResponse(
            location=request.location,
            windows=[
                pb2.ObservationWindow(
                    start_time=window.start_time.isoformat(),
                    end_time=window.end_time.isoformat(),
                    average_score=window.average_score,
                    rating=window.rating,
                    is_recommended=window.is_recommended,
                )
                for window in windows
            ],
        )

    async def StreamLocationComparison(self, request, context):
        if len(request.locations) < 2:
            await context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                "At least two locations are required for comparison.",
            )

        async def compare_location(location):
            try:
                forecast = await load_forecast(
                    location,
                    request.start_time,
                    request.end_time,
                )

                if not forecast:
                    raise ValueError("No weather data available.")

                best_weather = max(
                    forecast,
                    key=lambda item: evaluate_conditions(item).score,
                )
                result = evaluate_conditions(best_weather)

                return pb2.LocationComparisonResult(
                    location=location,
                    score=result.score,
                    rating=result.rating,
                    reasons=result.reasons,
                    best_time=best_weather.time.isoformat(),
                )

            except (ValueError, httpx.HTTPError, KeyError, TypeError) as exc:
                logger.warning(
                    "Comparison failed for %s: %s",
                    location.name,
                    exc,
                )
                return pb2.LocationComparisonResult(
                    location=location,
                    error=str(exc),
                )

        tasks = [
            asyncio.create_task(compare_location(location))
            for location in request.locations
        ]

        try:
            for completed in asyncio.as_completed(tasks):
                yield await completed
        finally:
            for task in tasks:
                if not task.done():
                    task.cancel()

            await asyncio.gather(*tasks, return_exceptions=True)


async def parse_time_or_none(value, context):
    try:
        return parse_time(value)
    except ValueError as exc:
        await context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(exc))


async def serve():
    server = grpc.aio.server()

    pb2_grpc.add_ObservationConditionsServiceServicer_to_server(
        ObservationConditionsService(),
        server,
    )

    address = f"{GRPC_HOST}:{GRPC_PORT}"
    server.add_insecure_port(address)

    await server.start()
    logger.info("gRPC server listening on %s", address)

    await server.wait_for_termination()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(serve())
