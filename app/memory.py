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


async def _connect_and_send(
    projector: PanasonicProjector, message: bytes, request: Request
):
    command = SEND_MESSAGE_PREAMBLE + message
    reader, writer = await asyncio.wait_for(
        asyncio.open_connection(projector.ip, DEFAULT_PORT),
        timeout=SOCKET_TIMEOUT,
    )
    response = await reader.read(BUFFER_SIZE)
    if WELCOME_MESSAGE not in response:
        projector.last_message = response.decode()
        await projector.save()
        await request.app.dispatch(
            "ws.broadcast.message", context={"message": "last_message"}
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
                "ws.broadcast.message", context={"message": "last_message"}
            )
            if ERROR_BUSY in r:
                await asyncio.sleep(RETRY_DELAY)
            elif r[2:] == message:
                break
            else:
                raise ProjectorCommandError(
                    f"{projector.name} unexpected response : {r}"
                )


async def recall_memory(
    memory: int,
    projector: PanasonicProjector,
    request: Request,
    retries: int = 0,
) -> None:
    message = _get_memory_message(memory)
    try:
        await _connect_and_send(projector=projector, message=message, request=request)
    except asyncio.TimeoutError as e:
        if retries <= MAX_RETRIES:
            await asyncio.sleep(RETRY_DELAY)
            retries += 1
            await recall_memory(
                memory, request=request, projector=projector, retries=retries
            )
        else:
            raise e


async def power_on(projector: PanasonicProjector, request: Request):
    message = b"PON\r"
    try:
        await _connect_and_send(projector=projector, message=message, request=request)
    except asyncio.TimeoutError:
        projector.last_message = "Projector might be offline"
        await projector.save()
        await request.app.dispatch(
            "ws.broadcast.message", context={"message": projector.last_message}
        )


async def power_off(projector: PanasonicProjector, request: Request, retries: int = 0):
    message = b"POF\r"
    try:
        await _connect_and_send(projector=projector, message=message, request=request)
    except asyncio.TimeoutError as e:
        if retries <= MAX_RETRIES:
            await asyncio.sleep(RETRY_DELAY)
            retries += 1
            await power_off(projector, request=request, retries=retries)
        else:
            raise e
