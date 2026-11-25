import asyncio
import logging
import time

import pywintypes
import win32con
import win32event
import win32file
import win32pipe
import winerror

from pydantic import ValidationError

from shared.constants import (
    MESSAGE_HEADER_SIZE,
    PipeOperation,
    ResponseStatus,
)
from shared.errors import (
    PipeError,
    PipeTimeoutError,
    SkyWatchError,
)
from shared.models.messages import (
    ErrorResponse,
    PipeRequest,
    PipeResponse,
)
from shared.models.requests import (
    DiscoveryRequest,
    RouteRequest,
)
from shared.protocol import (
    decode_header,
    decode_request,
    encode_message,
)
from worker.config import settings
from worker.services.discovery import DiscoveryService
from worker.services.routing import RoutingService


logger = logging.getLogger(__name__)

BUFFER_SIZE = 65536
IO_TIMEOUT = 15.0


class NamedPipeServer:
    def __init__(
        self,
        discovery_service: DiscoveryService,
        routing_service: RoutingService,
    ):
        self.discovery_service = discovery_service
        self.routing_service = routing_service
        self.pipe_path = settings.pipe_path
        self.running = False

    def serve_forever(self) -> None:
        """Accept and process incoming pipe connections."""

        self.running = True

        logger.info(
            "Named pipe server listening on %s",
            self.pipe_path,
        )

        try:
            while self.running:
                pipe = self._create_pipe()

                try:
                    self._connect(pipe)
                    self._handle_connection(pipe)

                except PipeError as exc:
                    logger.warning("%s", exc)

                except pywintypes.error as exc:
                    logger.warning("Named pipe error: %s", exc)

                finally:
                    self._close_pipe(pipe)

        except KeyboardInterrupt:
            logger.info("Stopping named pipe server.")

        finally:
            self.running = False

    def _create_pipe(self):
        """Create a duplex named pipe in byte mode."""

        return win32pipe.CreateNamedPipe(
            self.pipe_path,
            win32pipe.PIPE_ACCESS_DUPLEX
            | win32con.FILE_FLAG_OVERLAPPED,
            win32pipe.PIPE_TYPE_BYTE
            | win32pipe.PIPE_READMODE_BYTE
            | win32pipe.PIPE_WAIT
            | win32pipe.PIPE_REJECT_REMOTE_CLIENTS,
            1,
            BUFFER_SIZE,
            BUFFER_SIZE,
            0,
            None,
        )

    def _connect(self, pipe) -> None:
        """Wait for a client without blocking indefinitely."""

        overlapped = self._new_overlapped()

        try:
            result = win32pipe.ConnectNamedPipe(
                pipe,
                overlapped,
            )

            if result == winerror.ERROR_PIPE_CONNECTED:
                return

            if result == winerror.ERROR_IO_PENDING:
                self._wait_for_io(
                    pipe,
                    overlapped,
                    timeout=None,
                )

        finally:
            overlapped.hEvent.Close()

    def _handle_connection(self, pipe) -> None:
        """Read one request and send its corresponding response."""

        deadline = time.monotonic() + IO_TIMEOUT

        header = self._read_exact(
            pipe,
            MESSAGE_HEADER_SIZE,
            deadline,
        )

        message_size = decode_header(header)

        payload = self._read_exact(
            pipe,
            message_size,
            deadline,
        )

        request = decode_request(payload)

        logger.info(
            "Received %s [%s]",
            request.operation,
            request.request_id,
        )

        response = asyncio.run(
            self._process_request(request)
        )

        self._write_all(
            pipe,
            encode_message(response),
        )
        # Wait for confirmation that the client received the response.
        acknowledgement = self._read_exact(
            pipe,
            1,
            time.monotonic() + IO_TIMEOUT,
        )

        if acknowledgement != b"\x06":
            raise PipeError("Invalid response acknowledgement.")

    async def _process_request(
        self,
        request: PipeRequest,
    ) -> PipeResponse:
        """Execute an operation and construct a response."""

        try:
            async with asyncio.timeout(
                settings.pipe_response_timeout
            ):
                payload = await self._dispatch(request)

            return PipeResponse(
                request_id=request.request_id,
                status=ResponseStatus.SUCCESS,
                payload=payload,
            )

        except TimeoutError:
            error = ErrorResponse(
                code="PIPE_TIMEOUT",
                message="Operation timed out.",
            )

        except ValidationError:
            error = ErrorResponse(
                code="VALIDATION_ERROR",
                message="Invalid operation payload.",
            )

        except SkyWatchError as exc:
            logger.warning("%s", exc)

            error = ErrorResponse(
                code=exc.code,
                message="The requested operation failed.",
            )

        except Exception:
            logger.exception("Unexpected worker error.")

            error = ErrorResponse(
                code="INTERNAL_ERROR",
                message="An unexpected worker error occurred.",
            )

        return PipeResponse(
            request_id=request.request_id,
            status=ResponseStatus.ERROR,
            error=error,
        )

    async def _dispatch(self, request: PipeRequest) -> dict:
        """Dispatch the request to the appropriate service."""

        if request.operation == PipeOperation.PING:
            return {"available": True}

        if request.operation == PipeOperation.FIND_LOCATIONS:
            discovery_request = DiscoveryRequest.model_validate(
                request.payload
            )

            result = await self.discovery_service.discover(
                discovery_request
            )

            return result.model_dump(mode="json")

        if request.operation == PipeOperation.GET_ROUTE:
            route_request = RouteRequest.model_validate(
                request.payload
            )

            result = await self.routing_service.get_route(
                route_request
            )

            return result.model_dump(mode="json")

        raise PipeError("Unsupported operation.")

    def _read_exact(
        self,
        pipe,
        size: int,
        deadline: float,
    ) -> bytes:
        """Read exactly the requested number of bytes."""

        data = bytearray()

        while len(data) < size:
            remaining = size - len(data)
            chunk_size = min(remaining, BUFFER_SIZE)

            buffer = win32file.AllocateReadBuffer(
                chunk_size
            )

            overlapped = self._new_overlapped()

            try:
                timeout = deadline - time.monotonic()

                if timeout <= 0:
                    raise PipeTimeoutError(
                        "Pipe read timed out."
                    )

                win32file.ReadFile(
                    pipe,
                    buffer,
                    overlapped,
                )

                bytes_read = self._wait_for_io(
                    pipe,
                    overlapped,
                    timeout=timeout,
                )

                if bytes_read == 0:
                    raise PipeError(
                        "Client closed the connection."
                    )

                data.extend(
                    bytes(buffer)[:bytes_read]
                )

            finally:
                overlapped.hEvent.Close()

        return bytes(data)

    def _write_all(self, pipe, data: bytes) -> None:
        """Write the complete encoded message to the pipe."""

        offset = 0
        deadline = time.monotonic() + IO_TIMEOUT

        while offset < len(data):
            chunk = data[
                offset:offset + BUFFER_SIZE
            ]

            overlapped = self._new_overlapped()

            try:
                timeout = deadline - time.monotonic()

                if timeout <= 0:
                    raise PipeTimeoutError(
                        "Pipe write timed out."
                    )

                win32file.WriteFile(
                    pipe,
                    chunk,
                    overlapped,
                )

                bytes_written = self._wait_for_io(
                    pipe,
                    overlapped,
                    timeout=timeout,
                )

                if bytes_written == 0:
                    raise PipeError(
                        "Unable to write pipe data."
                    )

                offset += bytes_written

            finally:
                overlapped.hEvent.Close()

    @staticmethod
    def _new_overlapped():
        """Create an overlapped structure with its own event."""

        overlapped = pywintypes.OVERLAPPED()

        overlapped.hEvent = win32event.CreateEvent(
            None,
            True,
            False,
            None,
        )

        return overlapped

    @staticmethod
    def _wait_for_io(
        pipe,
        overlapped,
        timeout: float | None,
    ) -> int:
        """Wait for an I/O operation with cancellation support."""

        deadline = (
            time.monotonic() + timeout
            if timeout is not None
            else None
        )

        try:
            while True:
                wait_ms = 200

                if deadline is not None:
                    remaining = deadline - time.monotonic()

                    if remaining <= 0:
                        raise PipeTimeoutError(
                            "Pipe I/O operation timed out."
                        )

                    wait_ms = min(
                        wait_ms,
                        max(1, int(remaining * 1000)),
                    )

                result = win32event.WaitForSingleObject(
                    overlapped.hEvent,
                    wait_ms,
                )

                if result == win32event.WAIT_OBJECT_0:
                    return win32file.GetOverlappedResult(
                        pipe,
                        overlapped,
                        False,
                    )

                if result != win32event.WAIT_TIMEOUT:
                    raise PipeError(
                        "Unexpected pipe wait result."
                    )

        except BaseException:
            # Cancel pending I/O before releasing its resources.
            try:
                win32file.CancelIo(pipe)
            except pywintypes.error:
                pass

            try:
                win32file.GetOverlappedResult(
                    pipe,
                    overlapped,
                    True,
                )
            except pywintypes.error:
                pass

            raise

    @staticmethod
    def _close_pipe(pipe) -> None:
        """Release the Windows pipe handle."""

        pipe.Close()