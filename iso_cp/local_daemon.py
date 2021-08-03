from asyncio import IncompleteReadError, StreamReader, sleep
from asyncio.subprocess import DEVNULL, PIPE, create_subprocess_exec
from datetime import datetime
from os import sep
from pathlib import Path
from shlex import quote
from sys import stderr
from textwrap import dedent
from typing import Sequence, Tuple, cast

from .consts import BIN, NUL, TIME_FMT
from .copy import copy
from .logging import log
from .shared import join


def _tunnel_cmd(name: str) -> Tuple[Sequence[str], Sequence[str]]:
    lookup = {
        "cssh": (("ssh", "-T"), ()),
        "cdocker": (("docker", "exec"), ()),
    }
    return lookup[name]


def _tunneling_prog() -> str:
    canonical = BIN / "csshd"

    try:
        rel_path = canonical.relative_to(Path.home())
    except ValueError:
        return quote(str(canonical))
    else:
        return '"$HOME"' + quote(str(Path(sep) / rel_path))


async def _daemon(local: bool, name: str, args: Sequence[str]) -> None:
    prev, post = _tunnel_cmd(name)
    prog = _tunneling_prog()
    exe = (*prev, *args, *post, "sh", "-c", prog)
    proc = await create_subprocess_exec(*exe, stdin=DEVNULL, stdout=PIPE)
    stdout = cast(StreamReader, proc.stdout)

    msg = f"""
    Establishing link via:
    {join(exe)}
    """
    log.info("%s", dedent(msg))

    while True:
        if proc.returncode is not None:
            msg = f"Exited - {proc.returncode}"
            log.warn("%s", msg)
            break
        else:
            try:
                data = await stdout.readuntil(NUL)
            except IncompleteReadError:
                break
            else:
                time = datetime.now().strftime(TIME_FMT)
                await copy(local, args=args, data=data[:-1])

                msg = f"""

                -- RECV --
                {time}
                """
                log.info("%s", dedent(msg))


async def l_daemon(local: bool, name: str, args: Sequence[str]) -> int:
    while True:
        await _daemon(local, name=name, args=args)
        print("\a", end="", file=stderr)
        await sleep(1)
