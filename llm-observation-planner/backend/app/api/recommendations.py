from fastapi import APIRouter, HTTPException

from app.clients.openrouter import OpenRouterError
from app.models.requests import RecommendationRequest
from app.models.responses import RecommendationResponse
from app.services.recommendation_service import (
    RecommendationError,
    RecommendationService,
)


router = APIRouter(
    prefix="/api/recommendations",
    tags=["AI Recommendations"],
)


@router.post(
    "",
    response_model=RecommendationResponse,
)
def generate_recommendation(
    request: RecommendationRequest,
) -> RecommendationResponse:
    """Generate an AI recommendation for an astronomical event."""

    try:
        service = RecommendationService()
        return service.generate(request)

    except (RecommendationError, OpenRouterError) as exc:
        raise HTTPException(
            status_code=502,
            detail="AI recommendation service is currently unavailable.",
        ) from exc
