import asyncio
import os
import subprocess
import sys
import time

from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

import pywintypes
import win32con
import win32file
import win32pipe
import winerror

from shared.errors import PipeTimeoutError
import pytest

from app.pipes.client import NamedPipeClient
from shared.constants import PipeOperation, ResponseStatus
from shared.errors import PipeConnectionError
from shared.models.messages import PipeRequest


BACKEND_DIRECTORY = Path(__file__).resolve().parents[1]


@contextmanager
def running_worker():
    """Start a separate Worker process and clean it up."""

    process = subprocess.Popen(
        [sys.executable, "-m", "worker.main"],
        cwd=BACKEND_DIRECTORY,
        env=os.environ.copy(),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        yield process
    finally:
        if process.poll() is None:
            process.terminate()

            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


async def send_ping(client, connect_timeout=10):
    """Send a ping request through the named pipe."""

    request = PipeRequest(
        request_id=str(uuid4()),
        operation=PipeOperation.PING,
        payload={},
    )

    response = await client.send_request(
        request,
        connect_timeout=connect_timeout,
        response_timeout=5,
    )

    assert response.request_id == request.request_id
    assert response.status == ResponseStatus.SUCCESS
    assert response.payload == {"available": True}

    return response


def test_pipe_communication():
    """Verify communication between two separate processes."""

    client = NamedPipeClient()

    with running_worker() as worker:
        asyncio.run(send_ping(client))

        assert worker.poll() is None


def test_multiple_requests():
    """Verify that the named pipe can handle repeated requests."""

    client = NamedPipeClient()

    async def execute_requests():
        request_ids = set()

        for _ in range(5):
            response = await send_ping(client)

            assert response.request_id not in request_ids

            request_ids.add(response.request_id)

    with running_worker():
        asyncio.run(execute_requests())


def test_delayed_worker_start():
    """Verify that the client waits without blocking asyncio."""

    client = NamedPipeClient()

    async def execute():
        start_time = time.monotonic()

        # Start the request before the Worker exists.
        request_task = asyncio.create_task(
            send_ping(client, connect_timeout=10)
        )

        # The event loop must remain responsive.
        await asyncio.sleep(2)

        assert not request_task.done()

        # Start the Worker after the client has begun waiting.
        with running_worker():
            await request_task

        elapsed = time.monotonic() - start_time

        assert elapsed >= 2

        print(f"\nDelayed connection: {elapsed:.2f} s")

    asyncio.run(execute())


def test_connection_timeout():
    """Verify that waiting stops when no Worker is available."""

    client = NamedPipeClient()

    start_time = time.monotonic()

    with pytest.raises(PipeConnectionError):
        asyncio.run(
            send_ping(client, connect_timeout=3)
        )

    elapsed = time.monotonic() - start_time

    assert 2.8 <= elapsed <= 6

    print(f"\nConnection timeout: {elapsed:.2f} s")


def test_reconnection_after_worker_restart():
    """Verify reconnection after the Worker has been restarted."""

    client = NamedPipeClient()

    # First Worker instance.
    with running_worker():
        asyncio.run(send_ping(client))

    # The original Worker is no longer available.
    with pytest.raises(PipeConnectionError):
        asyncio.run(
            send_ping(client, connect_timeout=2)
        )

    # The same client must connect to a new Worker instance.
    with running_worker():
        asyncio.run(send_ping(client))


def test_reconnection_after_timeout():
    """Verify that a failed connection does not break the client."""

    client = NamedPipeClient()

    with pytest.raises(PipeConnectionError):
        asyncio.run(
            send_ping(client, connect_timeout=2)
        )

    # Communication must work after the previous timeout.
    with running_worker():
        asyncio.run(send_ping(client))

def test_active_io_timeout_and_recovery():
    """Verify cancellation of pending I/O and subsequent recovery."""

    client = NamedPipeClient()

    # Use an isolated pipe for the timeout scenario.
    original_pipe_path = client.pipe_path

    client.pipe_path = (
        rf"\\.\pipe\skywatch_timeout_test_{uuid4().hex}"
    )

    pipe = win32pipe.CreateNamedPipe(
        client.pipe_path,
        win32pipe.PIPE_ACCESS_DUPLEX,
        win32pipe.PIPE_TYPE_BYTE
        | win32pipe.PIPE_READMODE_BYTE
        | win32pipe.PIPE_WAIT,
        1,
        65536,
        65536,
        0,
        None,
    )

    request = PipeRequest(
        operation=PipeOperation.PING,
        payload={},
    )

    try:
        start_time = time.monotonic()

        # The pipe exists, but the server intentionally
        # does not send a response.
        with pytest.raises(PipeTimeoutError):
            asyncio.run(
                client.send_request(
                    request,
                    connect_timeout=3,
                    response_timeout=2,
                )
            )

        elapsed = time.monotonic() - start_time

        assert 1.8 <= elapsed <= 6

        print(
            f"\nActive I/O timeout: {elapsed:.2f} s"
        )

        # Inspect the server-side pipe without blocking.
        try:
            _, available, _ = win32pipe.PeekNamedPipe(
                pipe,
                0,
            )

            if available > 0:
                win32file.ReadFile(pipe, available)

            # Once buffered data is consumed, the closed
            # client connection must no longer be usable.
            with pytest.raises(pywintypes.error) as error:
                win32pipe.PeekNamedPipe(pipe, 0)

            assert error.value.winerror in {
                winerror.ERROR_BROKEN_PIPE,
                winerror.ERROR_NO_DATA,
                winerror.ERROR_PIPE_NOT_CONNECTED,
            }

        except pywintypes.error as error:
            assert error.winerror in {
                winerror.ERROR_BROKEN_PIPE,
                winerror.ERROR_NO_DATA,
                winerror.ERROR_PIPE_NOT_CONNECTED,
            }

    finally:
        pipe.Close()
        client.pipe_path = original_pipe_path

    # Verify that the same client remains usable.
    with running_worker():
        asyncio.run(send_ping(client))

    print("Communication successfully restored.")