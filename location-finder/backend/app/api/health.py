from fastapi import APIRouter

from app.pipes.client import NamedPipeClient
from shared.constants import PipeOperation, ResponseStatus
from shared.errors import PipeError
from shared.models.messages import PipeRequest
from shared.models.responses import HealthResponse


router = APIRouter(prefix="/api", tags=["Health"])

pipe_client = NamedPipeClient()


@router.get("/health", response_model=HealthResponse)
async def get_health() -> HealthResponse:
    """Check the availability of the API and Location Worker."""

    worker_available = False

    try:
        response = await pipe_client.send_request(
            request=PipeRequest(
                operation=PipeOperation.PING,
            ),
            connect_timeout=1.0,
            response_timeout=2.0,
        )

        worker_available = (
            response.status == ResponseStatus.SUCCESS
            and response.payload is not None
            and response.payload.get("available") is True
        )

    except PipeError:
        worker_available = False

    return HealthResponse(
        api_available=True,
        worker_available=worker_available,
    )