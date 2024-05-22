from contextlib import suppress
from itertools import chain
from os import environ
from shutil import which
from sys import stdout
from textwrap import dedent
from typing import Sequence

from iso_cp.consts import WRITE_PATH
from iso_cp.logging import log
from iso_cp.shared import call, run_in_executor


async def paste(local: bool, args: Sequence[str]) -> int:
    if which("pbpaste"):
        return await call("pbpaste")

    elif which("wl-copy") and "WAYLAND_DISPLAY" in environ:
        return await call("wl-paste")

    elif which("xclip") and "DISPLAY" in environ:
        xargs = (
            chain(args, ("-out",), (() if args else ("-selection", "clipboard")))
            if {*args}.isdisjoint({"-o", "-out"})
            else args
        )
        return await call("xclip", *xargs)

    elif which("xsel") and "DISPLAY" in environ:
        xargs = (
            chain(args, ("--output",))
            if {*args}.isdisjoint({"-o", "--output"})
            else args
        )
        return await call("xsel", *xargs)

    elif which("kitten"):
        return await call("kitten", "clipboard", "--get-clipboard")

    elif which("powershell.exe"):
        return await call("powershell.exe", "-command", "Get-Clipboard -Raw")

    elif which("tmux") and "TMUX" in environ:
        return await call("tmux", "save-buffer", "-")

    elif local:

        def cont() -> int:
            with suppress(FileNotFoundError):
                data = WRITE_PATH.read_bytes()
                stdout.buffer.write(data)
                stdout.buffer.flush()
            return 0

        return await run_in_executor(cont)

    else:
        msg = """
        ⚠️  No system clipboard detected ⚠️ 

        export ISOCP_USE_FILE=1 to use temp file
        """
        log.critical("%s", dedent(msg))
        return 1
