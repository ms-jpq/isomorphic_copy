from asyncio import FIRST_COMPLETED, ensure_future, sleep, wait
from asyncio.subprocess import DEVNULL, PIPE, create_subprocess_exec
from contextlib import contextmanager, suppress
from datetime import datetime
from os import environ, sep
from os.path import normpath
from pathlib import Path
from shlex import quote
from sys import stderr
from textwrap import dedent
from typing import Iterator, Sequence

from iso_cp.consts import BIN, INT_EXIT, TIME_FMT, TITLE, TOP_LV
from iso_cp.copy import copy
from iso_cp.logging import log
from iso_cp.shared import join, kill_children, read_all


def _tunneling_prog() -> str:
    home = Path.home()
    canonical = BIN / "cd"
    rel = canonical.relative_to(TOP_LV.parent)
    eh = f'exec "$HOME"{sep}'

    opt = home / ".local" / "opt" / rel
    with suppress(FileNotFoundError, ValueError):
        if opt.samefile(canonical):
            rel_path = opt.relative_to(home)
            return eh + quote(normpath(rel_path))

    xdg = environ.get("XDG_CONFIG_HOME", home / ".config") / rel
    with suppress(FileNotFoundError, ValueError):
        if xdg.samefile(canonical):
            rel_path = xdg.relative_to(home)
            return eh + quote(normpath(rel_path))

    with suppress(ValueError):
        rel_path = canonical.relative_to(home)
        return eh + quote(normpath(rel_path))

    return quote(normpath(canonical))


def _tunnel_cmd(name: str, args: Sequence[str]) -> Sequence[str]:
    sh = _tunneling_prog()
    if name == "cssh":
        return (
            "ssh",
            "-T",
            "-o",
            "ControlPath=none",
            "-o",
            "ForwardAgent=no",
            "-o",
            "ClearAllForwardings=yes",
            *args,
            sh,
        )
    elif name == "cdocker":
        return ("docker", "exec", *args, "sh", "-c", sh)
    else:
        assert False


async def _daemon(local: bool, name: str, args: Sequence[str]) -> int:
    cmds = _tunnel_cmd(name, args=args)
    proc = await create_subprocess_exec(
        *cmds, start_new_session=True, stdin=DEVNULL, stdout=PIPE
    )
    p_done = ensure_future(proc.wait())
    time = datetime.now().strftime(TIME_FMT)

    msg = f"""
    {time} | Establishing link via:
    {join(cmds)}
    """
    log.info("%s", dedent(msg))

    assert proc.stdout
    try:
        while True:
            p_data = ensure_future(read_all(proc.stdout))
            await wait((p_done, p_data), return_when=FIRST_COMPLETED)

            if p_data.done():
                data = await p_data
                if data:
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
            stderr.write(f"\x1B]2;{title}\x1B\\")
        else:
            stderr.write(f"\x1B]0;{title}\x1B\\")

        stderr.flush()

    cont(TITLE)
    try:
        yield None
    finally:
        cont("")


async def l_daemon(local: bool, name: str, args: Sequence[str]) -> int:
    with _title():
        while True:
            code = await _daemon(local, name=name, args=args)
            log.warn("%s", f"Exited - $? {code}")
            if code == INT_EXIT:
                return code
            else:
                # await run_in_executor(_bell)
                await sleep(1)
