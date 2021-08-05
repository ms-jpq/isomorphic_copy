from asyncio import FIRST_COMPLETED, IncompleteReadError, ensure_future, sleep, wait
from asyncio.subprocess import DEVNULL, PIPE, create_subprocess_exec
from contextlib import suppress
from datetime import datetime
from os import sep
from pathlib import Path
from shlex import quote
from sys import stderr
from textwrap import dedent
from typing import Sequence, Tuple

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


async def _daemon(local: bool, name: str, args: Sequence[str]) -> int:
    prev, post = _tunnel_cmd(name)
    prog = _tunneling_prog()
    exe = (*prev, *args, *post, "sh", "-c", prog)
    proc = await create_subprocess_exec(*exe, stdin=DEVNULL, stdout=PIPE)
    p_done = ensure_future(proc.wait())

    msg = f"""
    Establishing link via:
    {join(exe)}
    """
    log.info("%s", dedent(msg))
    try:
        assert proc.stdout
        while True:
            p_data = ensure_future(proc.stdout.readuntil(NUL))
            await wait((p_done, p_data), return_when=FIRST_COMPLETED)

            if p_data.done():
                with suppress(IncompleteReadError):
                    data = await p_data
                    await copy(local, args=args, data=data[:-1])

                    time = datetime.now().strftime(TIME_FMT)
                    msg = f"""
                    -- RECV --
                    {time}
                    """
                    log.info("%s", dedent(msg))

            if p_done.done():
                return await proc.wait()

    finally:
        with suppress(ProcessLookupError):
            proc.kill()
        await proc.wait()


async def l_daemon(local: bool, name: str, args: Sequence[str]) -> int:
    while True:
        code = await _daemon(local, name=name, args=args)
        log.warn("%s", f"Exited - $? {code}")
        print("\a", end="", file=stderr, flush=True)
        await sleep(1)
