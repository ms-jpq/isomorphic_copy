from asyncio import gather, open_unix_connection
from os import environ, sep
from pathlib import Path
from shutil import which
from sys import stdin
from typing import Optional, Sequence

from .consts import NUL, SOCKET_PATH, WRITE_PATH
from .shared import call


def _is_remote() -> bool:
    if "SSH_TTY" in environ:
        return True
    elif Path(sep, ".dockerenv").exists():
        return True
    else:
        return False


async def _rcp(data: bytes) -> None:
    try:
        conn = await open_unix_connection(str(SOCKET_PATH))
    except (FileNotFoundError, ConnectionRefusedError):
        pass
    else:
        _, writer = conn
        writer.write(data)
        writer.write(NUL)
        await writer.drain()


async def copy(local: bool, args: Sequence[str], data: Optional[bytes]) -> None:
    data = data or stdin.read().encode()
    tasks = []

    if _is_remote():
        tasks.append(_rcp(data))

    if "TMUX" in environ:
        tasks.append(call("tmux", "load-buffer", "-", stdin=data))

    if which("pbcopy"):
        tasks.append(call("pbcopy", stdin=data))

    if which("wl-copy") and "WAYLAND_DISPLAY" in environ:
        tasks.append(call("wl-copy", stdin=data))

    elif which("xclip") and "DISPLAY" in environ:
        tasks.append(call("xclip", *args, "-selection", "clipboard", stdin=data))
        tasks.append(call("xclip", *args, "-selection", "primary", stdin=data))

    elif local:
        WRITE_PATH.write_bytes(data)

    await gather(*tasks)

