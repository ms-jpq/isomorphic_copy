from asyncio import IncompleteReadError, LimitOverrunError, get_event_loop
from asyncio.streams import StreamReader
from asyncio.subprocess import DEVNULL, PIPE, create_subprocess_exec
from contextlib import suppress
from functools import partial
from os import getpgid, killpg
from pathlib import Path
from shlex import quote
from signal import Signals
from tempfile import NamedTemporaryFile
from typing import Any, Callable, Iterable, Optional, TypeVar

from iso_cp.consts import TMP, NUL

_T = TypeVar("_T")


def join(cmds: Iterable[str]) -> str:
    return " ".join(map(quote, cmds))


def kill_children(pid: int) -> None:
    killpg(getpgid(pid), Signals.SIGKILL)


async def call(prog: str, *args: str, stdin: Optional[bytes] = None) -> int:
    proc = await create_subprocess_exec(
        prog,
        *args,
        start_new_session=True,
        stdin=PIPE if stdin else DEVNULL,
    )
    try:
        if stdin:
            await proc.communicate(stdin)
        return await proc.wait()
    finally:
        with suppress(ProcessLookupError):
            kill_children(proc.pid)
        await proc.wait()


async def read_all(reader: StreamReader) -> bytes:
    acc = bytearray()
    while True:
        try:
            b = await reader.readuntil(NUL)
        except IncompleteReadError:
            break
        except LimitOverrunError as e:
            c = await reader.readexactly(e.consumed)
            acc.extend(c)
        else:
            acc.extend(b)
            break

    return acc


async def run_in_executor(f: Callable[..., _T], *args: Any, **kwargs: Any) -> _T:
    fn = partial(f, *args, **kwargs)
    return await get_event_loop().run_in_executor(None, fn)


def safe_write(path: Path, data: bytes) -> None:
    with NamedTemporaryFile(dir=TMP, delete=False) as fd:
        fd.write(data)

    Path(fd.name).replace(path)
