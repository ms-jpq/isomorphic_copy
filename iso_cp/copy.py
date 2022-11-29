import sys
from asyncio import gather, open_unix_connection
from base64 import b64encode
from os import environ, sep
from os.path import normpath
from pathlib import Path
from shutil import which
from sys import stderr
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
        _, writer = await open_unix_connection(normpath(SOCKET_PATH))
    except (FileNotFoundError, ConnectionRefusedError):
        pass
    else:
        try:
            writer.write(data)
            writer.write(NUL)
            await writer.drain()
        finally:
            writer.close()
            if sys.version_info > (3, 7):
                await writer.wait_closed()

    return 0


async def _osc52(tmux: bool, data: bytes) -> int:
    def cont() -> None:
        # TMUX wrap start
        if tmux:
            stderr.buffer.write(b"\x1BPtmux;")

        # TMUX escape `ESC`
        if tmux:
            stderr.buffer.write(b"\x1B")

        # OSC52 start
        stderr.buffer.write(b"\x1B]52;c;")

        # OSC52 body
        stderr.buffer.write(b64encode(data))

        # TMUX escape `ESC`
        if tmux:
            stderr.buffer.write(b"\x1B")

        # OSC52 end
        stderr.buffer.write(b"\x1B\\")

        # TMUX wrap end
        if tmux:
            stderr.buffer.write(b"\x1B\\")

        stderr.buffer.flush()

    if stderr.isatty():
        await run_in_executor(cont)
    return 0


async def copy(local: bool, args: Sequence[str], data: bytes) -> int:
    def c1() -> Iterator[Awaitable[int]]:
        tmux = "TMUX" in environ and which("tmux")

        if _is_remote():
            yield _rcp(data)
            yield _osc52(bool(tmux), data=data)

        if tmux:
            yield call(tmux, "load-buffer", "-", stdin=data)

        if which("pbcopy"):
            yield call("pbcopy", stdin=data)

        elif which("wl-copy") and "WAYLAND_DISPLAY" in environ:
            yield call("wl-copy", stdin=data)

        elif which("xclip") and "DISPLAY" in environ:
            yield call("xclip", *args, "-selection", "clipboard", stdin=data)
            yield call("xclip", *args, "-selection", "primary", stdin=data)

        elif which("clip.exe"):
            yield call("clip.exe", stdin=data)

        elif local:

            def c2() -> int:
                safe_write(WRITE_PATH, data=data)
                return 0

            yield run_in_executor(c2)

    cum: int = sum(await gather(*c1()))
    return cum
