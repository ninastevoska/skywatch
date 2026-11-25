from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator

from shared.constants import (
    PROTOCOL_VERSION,
    PipeOperation,
    ResponseStatus,
)


class ErrorResponse(BaseModel):
    code: str
    message: str


class PipeRequest(BaseModel):
    request_id: str = Field(
        default_factory=lambda: str(uuid4())
    )

    version: str = PROTOCOL_VERSION
    operation: PipeOperation

    payload: dict[str, Any] = Field(default_factory=dict)


class PipeResponse(BaseModel):
    request_id: str
    version: str = PROTOCOL_VERSION

    status: ResponseStatus

    payload: dict[str, Any] | None = None
    error: ErrorResponse | None = None

    @model_validator(mode="after")
    def validate_response(self) -> "PipeResponse":
        if self.status == ResponseStatus.SUCCESS:
            if self.payload is None or self.error is not None:
                raise ValueError(
                    "A successful response must contain a payload "
                    "and no error."
                )

        elif self.status == ResponseStatus.ERROR:
            if self.error is None or self.payload is not None:
                raise ValueError(
                    "An error response must contain an error "
                    "and no payload."
                )

        return self