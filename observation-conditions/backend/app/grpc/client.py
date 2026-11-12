import grpc

from proto import observation_conditions_pb2 as pb2
from proto import observation_conditions_pb2_grpc as pb2_grpc

from app.config import GRPC_HOST, GRPC_PORT


class ObservationConditionsClient:
    def __init__(self):
        self.address = f"{GRPC_HOST}:{GRPC_PORT}"

    def _channel(self):
        return grpc.aio.insecure_channel(self.address)

    async def get_weather_forecast(self, location, start_time, end_time):
        async with self._channel() as channel:
            stub = pb2_grpc.ObservationConditionsServiceStub(channel)

            request = pb2.WeatherForecastRequest(
                location=location,
                start_time=start_time,
                end_time=end_time,
            )

            return await stub.GetWeatherForecast(request)

    async def evaluate_conditions(self, location, time):
        async with self._channel() as channel:
            stub = pb2_grpc.ObservationConditionsServiceStub(channel)

            request = pb2.ConditionsRequest(
                location=location,
                time=time,
            )

            return await stub.EvaluateConditions(request)

    async def find_best_observation_windows(
        self, location, start_time, end_time
    ):
        async with self._channel() as channel:
            stub = pb2_grpc.ObservationConditionsServiceStub(channel)

            request = pb2.ObservationWindowsRequest(
                location=location,
                start_time=start_time,
                end_time=end_time,
            )

            return await stub.FindBestObservationWindows(request)

    async def stream_location_comparison(
        self, locations, start_time, end_time
    ):
        async with self._channel() as channel:
            stub = pb2_grpc.ObservationConditionsServiceStub(channel)

            request = pb2.LocationComparisonRequest(
                locations=locations,
                start_time=start_time,
                end_time=end_time,
            )

            async for result in stub.StreamLocationComparison(request):
                yield result
