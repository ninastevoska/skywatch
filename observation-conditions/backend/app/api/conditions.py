import json

import grpc
import httpx
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from google.protobuf.json_format import MessageToDict
from pydantic import BaseModel, Field

from proto import observation_conditions_pb2 as pb2

from app.clients.geocoding import search_locations
from app.grpc.client import ObservationConditionsClient


router = APIRouter(prefix="/api", tags=["Observation Conditions"])
grpc_client = ObservationConditionsClient()


class LocationInput(BaseModel):
    name: str = Field(min_length=1)
    latitude: float = Field(ge=-90, le=90, allow_inf_nan=False)
    longitude: float = Field(ge=-180, le=180, allow_inf_nan=False)


class ForecastInput(BaseModel):
    location: LocationInput
    start_time: str
    end_time: str


class ConditionsInput(BaseModel):
    location: LocationInput
    time: str


class ComparisonInput(BaseModel):
    locations: list[LocationInput] = Field(min_length=2, max_length=10)
    start_time: str
    end_time: str


def to_proto_location(location: LocationInput) -> pb2.Location:
    return pb2.Location(
        name=location.name,
        latitude=location.latitude,
        longitude=location.longitude,
    )



def to_dict(message) -> dict:
    return MessageToDict(
        message,
        preserving_proto_field_name=True,
        always_print_fields_with_no_presence=True,
    )



def raise_grpc_error(error: grpc.aio.AioRpcError):
    status_codes = {
        grpc.StatusCode.INVALID_ARGUMENT: 400,
        grpc.StatusCode.NOT_FOUND: 404,
        grpc.StatusCode.UNAVAILABLE: 503,
        grpc.StatusCode.DEADLINE_EXCEEDED: 504,
    }

    raise HTTPException(
        status_code=status_codes.get(error.code(), 500),
        detail=error.details() or "gRPC request failed.",
    )


@router.get("/locations")
async def locations(query: str = Query(min_length=2)):
    try:
        return await search_locations(query)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=502,
            detail="Location search service is unavailable.",
        ) from exc


@router.post("/forecast")
async def weather_forecast(request: ForecastInput):
    try:
        result = await grpc_client.get_weather_forecast(
            to_proto_location(request.location),
            request.start_time,
            request.end_time,
        )
        return to_dict(result)
    except grpc.aio.AioRpcError as exc:
        raise_grpc_error(exc)


@router.post("/conditions")
async def conditions(request: ConditionsInput):
    try:
        result = await grpc_client.evaluate_conditions(
            to_proto_location(request.location),
            request.time,
        )
        return to_dict(result)
    except grpc.aio.AioRpcError as exc:
        raise_grpc_error(exc)


@router.post("/windows")
async def observation_windows(request: ForecastInput):
    try:
        result = await grpc_client.find_best_observation_windows(
            to_proto_location(request.location),
            request.start_time,
            request.end_time,
        )
        return to_dict(result)
    except grpc.aio.AioRpcError as exc:
        raise_grpc_error(exc)


@router.post("/compare/stream")
async def compare_locations(request: ComparisonInput):
    async def generate_events():
        locations = [
            to_proto_location(location)
            for location in request.locations
        ]

        try:
            async for result in grpc_client.stream_location_comparison(
                locations,
                request.start_time,
                request.end_time,
            ):
                payload = json.dumps(to_dict(result))
                yield f"event: location\ndata: {payload}\n\n"

            yield "event: complete\ndata: {}\n\n"

        except grpc.aio.AioRpcError as exc:
            payload = json.dumps({
                "message": exc.details() or "Comparison failed."
            })
            yield f"event: error\ndata: {payload}\n\n"

    return StreamingResponse(
        generate_events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"},
    )
