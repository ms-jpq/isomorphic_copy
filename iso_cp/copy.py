import sys
from asyncio import gather, open_unix_connection
from base64 import b64encode
from os import environ, sep
from pathlib import Path
from shutil import which
from sys import stdout
from typing import Awaitable, Iterator, Sequence

from .consts import NUL, SOCKET_PATH, WRITE_PATH
from .shared import call, run_in_executor, safe_write


def _is_remote() -> bool:
    if "SSH_TTY" in environ:
        return True
    elif Path(sep, ".dockerenv").exists():
        return True
    else:
        return False


async def _rcp(data: bytes) -> int:
    try:
        _, writer = await open_unix_connection(str(SOCKET_PATH))
    except (FileNotFoundError, ConnectionRefusedError):
        pass
    else:
        writer.write(data)
        writer.write(NUL)
        await writer.drain()
        writer.close()
        if sys.version_info > (3, 7):
            await writer.wait_closed()

    return 0


async def _osc52(data: bytes) -> int:
    def cont() -> None:
        stdout.buffer.write(b"\033]52;c;")
        stdout.buffer.write(b64encode(data))
        stdout.buffer.write(b"\a")
        stdout.buffer.flush()

    await run_in_executor(cont)
    return 0


async def copy(local: bool, args: Sequence[str], data: bytes) -> int:
    def c1() -> Iterator[Awaitable[int]]:
        if _is_remote():
            yield _rcp(data)

        if which("tmux") and "TMUX" in environ:
            yield call("tmux", "load-buffer", "-", stdin=data)

        # if "SSH_TTY" in environ:
        #     yield _osc52(data)

        if which("pbcopy"):
            yield call("pbcopy", stdin=data)

        elif which("wl-copy") and "WAYLAND_DISPLAY" in environ:
            yield call("wl-copy", stdin=data)

        elif which("xclip") and "DISPLAY" in environ:
            yield call("xclip", *args, "-selection", "clipboard", stdin=data)
            yield call("xclip", *args, "-selection", "primary", stdin=data)

        elif local:

            def c2() -> int:
                safe_write(WRITE_PATH, data=data)
                return 0

            yield run_in_executor(c2)

    cum = sum(await gather(*c1()))
    return cum
