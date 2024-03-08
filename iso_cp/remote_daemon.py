import sys
from asyncio import StreamReader, StreamWriter, start_unix_server
from os.path import normcase
from sys import stdout

from iso_cp.consts import LIMIT, NUL, SOCKET_PATH
from iso_cp.shared import run_in_executor


async def r_daemon() -> int:
    async def handler(reader: StreamReader, _: StreamWriter) -> None:
        data = await reader.readuntil(NUL)

        def cont() -> None:
            stdout.buffer.write(data)
            stdout.buffer.flush()

        await run_in_executor(cont)

    server = await start_unix_server(handler, normcase(SOCKET_PATH), limit=LIMIT)

    if sys.version_info > (3, 7):
        async with server:
            await server.serve_forever()
    else:
        try:
            await server.wait_closed()
        finally:
            server.close()
            await server.wait_closed()

    return 1
