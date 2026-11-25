import struct

from pydantic import ValidationError

from shared.config import shared_settings
from shared.constants import (
    MESSAGE_HEADER_SIZE,
    PROTOCOL_VERSION,
)
from shared.errors import PipeProtocolError
from shared.models.messages import PipeRequest, PipeResponse


# Unsigned 4-byte integer in network byte order (big-endian).
HEADER_FORMAT = "!I"


def encode_message(
    message: PipeRequest | PipeResponse,
) -> bytes:
    """Serialize a message and prepend its payload length."""

    payload = message.model_dump_json().encode("utf-8")

    validate_message_size(len(payload))

    header = struct.pack(
        HEADER_FORMAT,
        len(payload),
    )

    return header + payload


def decode_header(header: bytes) -> int:
    """Extract the payload length from a message header."""

    if len(header) != MESSAGE_HEADER_SIZE:
        raise PipeProtocolError(
            "Invalid message header size."
        )

    message_size = struct.unpack(
        HEADER_FORMAT,
        header,
    )[0]

    validate_message_size(message_size)

    return message_size


def decode_request(payload: bytes) -> PipeRequest:
    """Deserialize and validate a pipe request."""

    validate_message_size(len(payload))

    try:
        request = PipeRequest.model_validate_json(payload)

    except ValidationError as exc:
        raise PipeProtocolError(
            "Invalid request payload."
        ) from exc

    validate_protocol_version(request.version)

    return request


def decode_response(payload: bytes) -> PipeResponse:
    """Deserialize and validate a pipe response."""

    validate_message_size(len(payload))

    try:
        response = PipeResponse.model_validate_json(payload)

    except ValidationError as exc:
        raise PipeProtocolError(
            "Invalid response payload."
        ) from exc

    validate_protocol_version(response.version)

    return response


def validate_message_size(message_size: int) -> None:
    """Reject empty or excessively large messages."""

    if message_size <= 0:
        raise PipeProtocolError(
            "Message payload cannot be empty."
        )

    if message_size > shared_settings.pipe_max_message_size:
        raise PipeProtocolError(
            "Message exceeds the maximum allowed size."
        )


def validate_protocol_version(version: str) -> None:
    """Verify that both processes use the same protocol version."""

    if version != PROTOCOL_VERSION:
        raise PipeProtocolError(
            f"Unsupported protocol version: {version}."
        )