from asyncio import gather, open_unix_connection
from os import environ, sep
from pathlib import Path
from shutil import which
from sys import stdin
from typing import Awaitable, Iterator, Optional, Sequence

from .consts import NUL, SOCKET_PATH, WRITE_PATH
from .shared import call


def _is_remote() -> bool:
    if "SSH_TTY" in environ:
        return True
    elif Path(sep, ".dockerenv").exists():
        return True
    else:
        return False


async def _rcp(data: bytes) -> int:
    try:
        conn = await open_unix_connection(str(SOCKET_PATH))
    except (FileNotFoundError, ConnectionRefusedError):
        pass
    else:
        _, writer = conn
        writer.write(data)
        writer.write(NUL)
        await writer.drain()
    return 0


async def _zero() -> int:
    return 0


async def copy(local: bool, args: Sequence[str], data: Optional[bytes]) -> None:
    def cont() -> Iterator[Awaitable[int]]:
        content = data or stdin.read().encode()
        if _is_remote():
            yield _rcp(content)

        if "TMUX" in environ:
            yield call("tmux", "load-buffer", "-", stdin=content)

        if which("pbcopy"):
            yield call("pbcopy", stdin=content)

        if which("wl-copy") and "WAYLAND_DISPLAY" in environ:
            yield call("wl-copy", stdin=content)

        elif which("xclip") and "DISPLAY" in environ:
            yield call("xclip", *args, "-selection", "clipboard", stdin=content)
            yield call("xclip", *args, "-selection", "primary", stdin=content)

        elif local:
            WRITE_PATH.write_bytes(content)
            yield _zero()

    codes = await gather(cont())

