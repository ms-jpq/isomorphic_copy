from asyncio import FIRST_COMPLETED, IncompleteReadError, ensure_future, sleep, wait
from asyncio.subprocess import DEVNULL, PIPE, create_subprocess_exec
from contextlib import contextmanager, suppress
from datetime import datetime
from os import environ, sep
from os.path import normpath
from pathlib import Path
from shlex import quote
from sys import stdout
from textwrap import dedent
from typing import Iterator, Sequence

from .consts import BIN, LIMIT, NUL, TIME_FMT, TITLE
from .copy import copy
from .logging import log
from .shared import join, kill_children, run_in_executor


def _tunneling_prog() -> str:
    canonical = BIN / "csshd"

    try:
        rel_path = canonical.relative_to(Path.home())
    except ValueError:
        return quote(normpath(canonical))
    else:
        return 'exec "$HOME"' + quote(normpath(Path(sep) / rel_path))


def _tunnel_cmd(name: str, args: Sequence[str]) -> Sequence[str]:
    sh = _tunneling_prog()
    if name == "cssh":
        return ("ssh", "-T", *args, sh)
    elif name == "cdocker":
        return ("docker", "exec", *args, "sh", "-c", sh)
    else:
        assert False


async def _daemon(local: bool, name: str, args: Sequence[str]) -> int:
    cmds = _tunnel_cmd(name, args=args)
    proc = await create_subprocess_exec(
        *cmds, start_new_session=True, stdin=DEVNULL, stdout=PIPE, limit=LIMIT
    )
    p_done = ensure_future(proc.wait())
    time = datetime.now().strftime(TIME_FMT)

    msg = f"""
    {time} | Establishing link via:
    {join(cmds)}
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
            kill_children(proc.pid)
        await proc.wait()


@contextmanager
def _title() -> Iterator[None]:
    def cont(title: str) -> None:
        if "TMUX" in environ:
            stdout.write(f"\x1Bk{title}\x1B\\")
        else:
            stdout.write(f"\x1B]0;{title}\x1B\\")

        stdout.flush()

    cont(TITLE)
    try:
        yield None
    finally:
        cont("")


def _bell() -> None:
    stdout.write("\a")
    stdout.flush()


async def l_daemon(local: bool, name: str, args: Sequence[str]) -> int:
    with _title():
        while True:
            code = await _daemon(local, name=name, args=args)
            log.warn("%s", f"Exited - $? {code}")
            await run_in_executor(_bell)
            await sleep(1)
