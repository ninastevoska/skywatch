import asyncio
import time

import pywintypes
import win32con
import win32event
import win32file
import winerror

from app.config import settings
from shared.constants import MESSAGE_HEADER_SIZE
from shared.errors import (
    PipeError,
    PipeConnectionError,
    PipeTimeoutError,
    PipeProtocolError,
)
from shared.models.messages import PipeRequest, PipeResponse
from shared.protocol import (
    encode_message,
    decode_header,
    decode_response,
)


BUFFER_SIZE = 65536
IO_TIMEOUT = 15.0


class NamedPipeClient:
    def __init__(self):
        self.pipe_path = settings.pipe_path

    async def send_request(
        self,
        request: PipeRequest,
        connect_timeout: float | None = None,
        response_timeout: float | None = None,
    ) -> PipeResponse:
        """Send a request without blocking the asyncio event loop."""

        return await asyncio.to_thread(
            self._exchange,
            request,
            connect_timeout,
            response_timeout,
        )

    def _exchange(
        self,
        request: PipeRequest,
        connect_timeout: float | None,
        response_timeout: float | None,
    ) -> PipeResponse:
        """Perform a complete request-response exchange."""

        encoded_request = encode_message(request)

        pipe = self._connect(
            connect_timeout
            if connect_timeout is not None
            else settings.pipe_connect_timeout
        )

        try:
            self._write_all(
                pipe,
                encoded_request,
                time.monotonic() + IO_TIMEOUT,
            )

            timeout = (
                response_timeout
                if response_timeout is not None
                else settings.pipe_response_timeout + IO_TIMEOUT
            )

            deadline = time.monotonic() + timeout

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

            response = decode_response(payload)

            if response.request_id != request.request_id:
                raise PipeProtocolError(
                    "Response request ID does not match."
                )

            # Confirm that the complete response was received.
            self._write_all(
                pipe,
                b"\x06",
                time.monotonic() + IO_TIMEOUT,
            )

            return response

        except pywintypes.error as exc:
            raise PipeError(
                "Named pipe communication failed."
            ) from exc

        finally:
            pipe.Close()

    def _connect(self, timeout: float):
        """Retry connecting until the worker becomes available."""

        deadline = time.monotonic() + timeout

        retryable_errors = {
            winerror.ERROR_FILE_NOT_FOUND,
            winerror.ERROR_PIPE_BUSY,
        }

        while True:
            try:
                return win32file.CreateFile(
                    self.pipe_path,
                    win32con.GENERIC_READ
                    | win32con.GENERIC_WRITE,
                    0,
                    None,
                    win32con.OPEN_EXISTING,
                    win32con.FILE_FLAG_OVERLAPPED,
                    None,
                )

            except pywintypes.error as exc:
                if exc.winerror not in retryable_errors:
                    raise PipeConnectionError(
                        "Unable to open the named pipe."
                    ) from exc

                remaining = deadline - time.monotonic()

                if remaining <= 0:
                    raise PipeConnectionError(
                        "Location Worker is currently unavailable."
                    ) from exc

                time.sleep(
                    min(
                        settings.pipe_retry_interval,
                        remaining,
                    )
                )

    def _read_exact(
        self,
        pipe,
        size: int,
        deadline: float,
    ) -> bytes:
        """Read exactly the requested number of bytes."""

        data = bytearray()

        while len(data) < size:
            chunk_size = min(
                size - len(data),
                BUFFER_SIZE,
            )

            buffer = win32file.AllocateReadBuffer(
                chunk_size
            )

            overlapped = self._new_overlapped()

            try:
                if time.monotonic() >= deadline:
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
                    deadline,
                )

                if bytes_read == 0:
                    raise PipeError(
                        "Worker closed the connection."
                    )

                data.extend(
                    bytes(buffer)[:bytes_read]
                )

            finally:
                overlapped.hEvent.Close()

        return bytes(data)

    def _write_all(
        self,
        pipe,
        data: bytes,
        deadline: float,
    ) -> None:
        """Write all bytes to the named pipe."""

        offset = 0

        while offset < len(data):
            chunk = data[
                offset:offset + BUFFER_SIZE
            ]

            overlapped = self._new_overlapped()

            try:
                if time.monotonic() >= deadline:
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
                    deadline,
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
        deadline: float,
    ) -> int:
        """Wait for an I/O operation until its deadline."""

        try:
            while True:
                remaining = deadline - time.monotonic()

                if remaining <= 0:
                    raise PipeTimeoutError(
                        "Pipe I/O operation timed out."
                    )

                wait_ms = min(
                    200,
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
            # Cancel pending I/O before releasing resources.
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