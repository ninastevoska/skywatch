import asyncio
from datetime import date, datetime, time, timedelta, timezone

from proto import observation_conditions_pb2 as pb2

from app.grpc.client import ObservationConditionsClient


async def main():
    client = ObservationConditionsClient()

    maribor = pb2.Location(
        name="Maribor",
        latitude=46.55583,
        longitude=15.64593,
    )
    ljubljana = pb2.Location(
        name="Ljubljana",
        latitude=46.05108,
        longitude=14.50513,
    )

    today = date.today()
    start = datetime.combine(today, time(18), tzinfo=timezone.utc)
    end = start + timedelta(hours=6)

    print("\n1. WEATHER FORECAST")
    forecast = await client.get_weather_forecast(
        maribor, start.isoformat(), end.isoformat()
    )
    print(f"Received {len(forecast.hourly)} hourly forecasts.")

    print("\n2. CONDITIONS EVALUATION")
    conditions = await client.evaluate_conditions(
        maribor, start.isoformat()
    )
    print(f"{conditions.score}/100 - {conditions.rating}")

    print("\n3. OBSERVATION WINDOWS")
    windows = await client.find_best_observation_windows(
        maribor, start.isoformat(), end.isoformat()
    )
    for window in windows.windows:
        print(
            f"{window.start_time} to {window.end_time}: "
            f"{window.average_score}/100 "
            f"(recommended: {window.is_recommended})"
        )

    print("\n4. LOCATION COMPARISON STREAM")
    async for result in client.stream_location_comparison(
        [maribor, ljubljana],
        start.isoformat(),
        end.isoformat(),
    ):
        if result.error:
            print(f"{result.location.name}: ERROR - {result.error}")
        else:
            print(
                f"{result.location.name}: "
                f"{result.score}/100 - {result.rating}"
            )


if __name__ == "__main__":
    asyncio.run(main())
