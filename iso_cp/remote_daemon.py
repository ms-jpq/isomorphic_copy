from asyncio import StreamReader, StreamWriter, start_unix_server
from sys import stdout

from .consts import NUL, SOCKET_PATH
from .shared import run_in_executor


async def r_daemon() -> int:
    async def handler(reader: StreamReader, _: StreamWriter) -> None:
        data = await reader.readuntil(NUL)
        await run_in_executor(stdout.buffer.write, data)
        await run_in_executor(stdout.buffer.flush)

    server = await start_unix_server(handler, str(SOCKET_PATH))
    try:
        await server.wait_closed()
    finally:
        server.close()
        await server.wait_closed()
    return 1
