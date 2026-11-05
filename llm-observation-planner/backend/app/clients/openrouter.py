from openai import APIStatusError, OpenAI, OpenAIError
from pydantic import BaseModel

from app.config import get_settings


class OpenRouterError(Exception):
    """Error raised when an OpenRouter request fails."""


class OpenRouterClient:
    """Client for generating structured AI responses via OpenRouter."""

    def __init__(self) -> None:
        settings = get_settings()

        if not settings.openrouter_api_key:
            raise OpenRouterError(
                "OpenRouter API key is not configured."
            )

        self.model = settings.openrouter_model

        self.client = OpenAI(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
            timeout=60.0,
            max_retries=0,
        )

    def generate_json(
        self,
        messages: list[dict[str, str]],
        response_model: type[BaseModel],
    ) -> str:
        """Generate a structured JSON response via OpenRouter."""

        response_schema = response_model.model_json_schema()

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.2,
                max_tokens=2000,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": response_model.__name__,
                        "strict": False,
                        "schema": response_schema,
                    },
                },
            )

        except APIStatusError as exc:
            raise OpenRouterError(
                f"OpenRouter HTTP {exc.status_code}: {exc.message}"
            ) from exc

        except OpenAIError as exc:
            raise OpenRouterError(
                f"OpenRouter request failed: "
                f"{type(exc).__name__}: {exc}"
            ) from exc

        if not completion.choices:
            raise OpenRouterError(
                "OpenRouter returned no response choices."
            )

        choice = completion.choices[0]

        if choice.finish_reason == "length":
            raise OpenRouterError(
                "The AI response exceeded the output token limit."
            )

        if choice.finish_reason != "stop":
            raise OpenRouterError(
                "The AI response did not finish normally."
            )

        content = choice.message.content

        if not content or not content.strip():
            raise OpenRouterError(
                "OpenRouter returned an empty response."
            )

        return content