import asyncio

from sanic import Request
from .models import PanasonicProjector


class ProjectorConnectionError(Exception):
    pass


class ProjectorCommandError(Exception):
    pass


SEND_MESSAGE_PREAMBLE = b"20ADZZ;"
WELCOME_MESSAGE = b"NTCONTROL 0\r"
ERROR_BUSY = b"ER401"

DEFAULT_PORT = 1024
SOCKET_TIMEOUT = 3
BUFFER_SIZE = 1024
MAX_RETRIES = 12
RETRY_DELAY = 3
RETRIES = 0


def _get_memory_message(memory: int) -> bytes:
    memory = memory - 1
    if not 0 <= memory <= 9:
        raise ValueError("Lens Memory must be between 1 and 10")
    return f"VXX:LNMI1=+0000{memory}\r".encode()


async def _send_command(
    command: bytes,
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
) -> bytes:
    writer.write(command)
    await writer.drain()
    r = await reader.read(BUFFER_SIZE)
    return r


async def recall_memory(
    memory: int,
    projector: PanasonicProjector,
    request: Request,
    retries: int = 0,
) -> None:
    message = _get_memory_message(memory)
    command = SEND_MESSAGE_PREAMBLE + message
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(projector.ip, DEFAULT_PORT),
            timeout=SOCKET_TIMEOUT,
        )
        response = await reader.read(BUFFER_SIZE)
        if WELCOME_MESSAGE not in response:
            projector.last_message = response.decode()
            await projector.save()
            await request.app.dispatch(
                "ws.update.last_message", context={"projector_id": projector.id}
            )
            raise ProjectorConnectionError(
                f"{projector.name} connection error: Unexpected welcome message {response}"
            )
        else:
            retries = 0
            while retries <= MAX_RETRIES:
                r = await _send_command(command, reader=reader, writer=writer)
                projector.last_message = r.decode()
                await projector.save()
                await request.app.dispatch(
                    "ws.update.last_message", context={"projector_id": projector.id}
                )
                if ERROR_BUSY in r:
                    await asyncio.sleep(RETRY_DELAY)
                elif r == message:
                    break
                else:
                    raise ProjectorCommandError(
                        f"{projector.name} unexpected response : {r}"
                    )

    except asyncio.TimeoutError as e:
        if retries <= MAX_RETRIES:
            retries += 1
            await recall_memory(
                memory, request=request, projector=projector, retries=retries
            )
        else:
            raise e


async def _connect(
    p: PanasonicProjector, port: int = DEFAULT_PORT
) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
    r = w = None
    try:
        fut = asyncio.open_connection(p.ip, DEFAULT_PORT)
        r, w = await asyncio.wait_for(fut, timeout=SOCKET_TIMEOUT)

    except asyncio.TimeoutError:
        r = w = None
        raise asyncio.TimeoutError
    except OSError as e:
        r = w = None
        raise ProjectorConnectionError(f"OSError connecting to {p.name} : {e}")
    return r, w
