from itertools import chain
from os import environ, linesep
from shutil import which
from sys import stderr, stdout
from typing import Sequence

from .consts import WRITE_PATH
from .shared import call


async def paste(local: bool, args: Sequence[str]) -> int:
    if which("pbpaste"):
        return await call("pbpaste")

    elif which("wl-copy") and "WAYLAND_DISPLAY" in environ:
        return await call("wl-paste")

    elif which("xclip") and "DISPLAY" in environ:
        xargs = chain(args, ("-out",)) if {*args}.isdisjoint({"-o", "-out"}) else args
        # primary clipboard ???
        return await call("xclip", *xargs, "-selection", "clipboard")

    elif "TMUX" in environ:
        return await call("tmux", "save-buffer", "-")

    elif local:
        if WRITE_PATH.exists():
            data = WRITE_PATH.read_bytes()
            stdout.buffer.write(data)
            stdout.buffer.flush()

        return 0
    else:
        print(
            "⚠️  No system clipboard detected ⚠️",
            "export ISOCP_USE_FILE=1 to use temp file",
            sep=linesep * 2,
            file=stderr,
        )
        return 1

