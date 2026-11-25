import struct

import pytest

from shared.constants import (
    MESSAGE_HEADER_SIZE,
    PROTOCOL_VERSION,
    PipeOperation,
    ResponseStatus,
)

from shared.errors import PipeProtocolError

from shared.models.messages import (
    ErrorResponse,
    PipeRequest,
    PipeResponse,
)

from shared.protocol import (
    encode_message,
    decode_header,
    decode_request,
    decode_response,
)


def test_request_roundtrip():
    """Verify request encoding and decoding."""

    request = PipeRequest(
        operation=PipeOperation.FIND_LOCATIONS,
        payload={
            "origin": {
                "name": "Maribor",
                "coordinates": {
                    "latitude": 46.5547,
                    "longitude": 15.6459,
                },
            },
        },
    )

    encoded = encode_message(request)

    header = encoded[:MESSAGE_HEADER_SIZE]
    body = encoded[MESSAGE_HEADER_SIZE:]

    assert decode_header(header) == len(body)

    decoded = decode_request(body)

    assert decoded == request
    assert decoded.version == PROTOCOL_VERSION


def test_success_response_roundtrip():
    """Verify successful response encoding and decoding."""

    response = PipeResponse(
        request_id="test-request-1",
        status=ResponseStatus.SUCCESS,
        payload={
            "available": True,
        },
    )

    encoded = encode_message(response)

    decoded = decode_response(
        encoded[MESSAGE_HEADER_SIZE:]
    )

    assert decoded == response
    assert decoded.error is None


def test_error_response_roundtrip():
    """Verify error response encoding and decoding."""

    response = PipeResponse(
        request_id="test-request-2",
        status=ResponseStatus.ERROR,
        error=ErrorResponse(
            code="EXTERNAL_API_ERROR",
            message="The external service is unavailable.",
        ),
    )

    encoded = encode_message(response)

    decoded = decode_response(
        encoded[MESSAGE_HEADER_SIZE:]
    )

    assert decoded == response
    assert decoded.payload is None


def test_unicode_roundtrip():
    """Verify preservation of international characters."""

    request = PipeRequest(
        operation=PipeOperation.FIND_LOCATIONS,
        payload={
            "locations": [
                "Razgledi\u0161\u010de",
                "\u0160marna gora",
                "\u010crni vrh",
                "\u041e\u0445\u0440\u0438\u0434",
            ],
        },
    )

    encoded = encode_message(request)

    header = encoded[:MESSAGE_HEADER_SIZE]
    body = encoded[MESSAGE_HEADER_SIZE:]

    assert decode_header(header) == len(body)

    decoded = decode_request(body)

    assert decoded.payload == request.payload


def test_invalid_header_length():
    """Reject incomplete message headers."""

    invalid_header = b"\x00\x01"

    with pytest.raises(PipeProtocolError):
        decode_header(invalid_header)


def test_zero_message_size():
    """Reject messages with an empty body."""

    invalid_header = struct.pack("!I", 0)

    with pytest.raises(PipeProtocolError):
        decode_header(invalid_header)


def test_excessive_message_size():
    """Reject messages exceeding the configured size limit."""

    invalid_header = struct.pack("!I", 2**32 - 1)

    with pytest.raises(PipeProtocolError):
        decode_header(invalid_header)


def test_invalid_json():
    """Reject malformed JSON messages."""

    invalid_body = b"invalid JSON"

    with pytest.raises(PipeProtocolError):
        decode_request(invalid_body)


def test_invalid_request_structure():
    """Reject JSON that does not match the request model."""

    invalid_body = b'{"unexpected_field": true}'

    with pytest.raises(PipeProtocolError):
        decode_request(invalid_body)


def test_unsupported_protocol_version():
    """Reject requests using unsupported protocol versions."""

    request = PipeRequest(
        operation=PipeOperation.PING,
        payload={},
    )

    invalid_request = request.model_copy(
        update={"version": "99.0"}
    )

    body = invalid_request.model_dump_json().encode("utf-8")

    with pytest.raises(PipeProtocolError):
        decode_request(body)