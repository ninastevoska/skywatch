from pydantic import ValidationError

from app.clients.openrouter import OpenRouterClient, OpenRouterError
from app.models.requests import RecommendationRequest
from app.models.responses import RecommendationResponse
from app.services.prompt_builder import (
    RESPONSE_MODELS,
    build_messages,
)


class RecommendationError(Exception):
    """Error raised when an AI recommendation cannot be generated."""


class RecommendationService:
    """Orchestrates AI recommendation generation and validation."""

    def __init__(self, client: OpenRouterClient | None = None) -> None:
        self.client = client if client is not None else OpenRouterClient()

    def generate(
        self,
        request: RecommendationRequest,
    ) -> RecommendationResponse:
        """Generate and validate an astronomical recommendation."""

        feature = request.preferences.feature
        response_model = RESPONSE_MODELS[feature]
        messages = build_messages(request)

        try:
            json_text = self.client.generate_json(
                messages=messages,
                response_model=response_model,
            )

            result = response_model.model_validate_json(json_text)

        except OpenRouterError as exc:
            raise RecommendationError(
                "The AI provider could not generate a recommendation."
            ) from exc

        except ValidationError as exc:
            raise RecommendationError(
                "The AI provider returned an invalid JSON response."
            ) from exc

        return RecommendationResponse(
            feature=feature,
            result=result,
        )
