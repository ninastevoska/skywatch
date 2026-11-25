from fastapi import APIRouter, HTTPException
from pydantic import ValidationError

from app.pipes.client import NamedPipeClient
from shared.constants import PipeOperation, ResponseStatus
from shared.errors import (
    PipeError,
    PipeConnectionError,
    PipeTimeoutError,
)
from shared.models.messages import PipeRequest
from shared.models.requests import DiscoveryRequest
from shared.models.responses import DiscoveryResponse


router = APIRouter(prefix="/api", tags=["Discovery"])

pipe_client = NamedPipeClient()


@router.post("/discover", response_model=DiscoveryResponse)
async def discover_locations(
    request: DiscoveryRequest,
) -> DiscoveryResponse:
    """Discover reachable observation locations through the worker."""

    pipe_request = PipeRequest(
        operation=PipeOperation.FIND_LOCATIONS,
        payload=request.model_dump(mode="json"),
    )

    try:
        response = await pipe_client.send_request(pipe_request)

    except PipeConnectionError as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "code": exc.code,
                "message": exc.message,
            },
        ) from exc

    except PipeTimeoutError as exc:
        raise HTTPException(
            status_code=504,
            detail={
                "code": exc.code,
                "message": exc.message,
            },
        ) from exc

    except PipeError as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "code": exc.code,
                "message": "Communication with the worker failed.",
            },
        ) from exc

    if response.status == ResponseStatus.ERROR:
        error = response.error

        status_code = {
            "VALIDATION_ERROR": 422,
            "EXTERNAL_API_ERROR": 502,
            "PIPE_TIMEOUT": 504,
        }.get(error.code, 500)

        raise HTTPException(
            status_code=status_code,
            detail=error.model_dump(),
        )

    try:
        return DiscoveryResponse.model_validate(
            response.payload
        )

    except ValidationError as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "code": "INVALID_WORKER_RESPONSE",
                "message": "The worker returned an invalid response.",
            },
        ) from exc