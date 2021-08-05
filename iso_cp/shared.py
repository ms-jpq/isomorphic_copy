from asyncio import get_event_loop
from asyncio.subprocess import DEVNULL, PIPE, create_subprocess_exec
from contextlib import suppress
from functools import partial
from shlex import quote
from typing import Any, Callable, Iterable, Optional, TypeVar

_T = TypeVar("_T")


def join(cmds: Iterable[str]) -> str:
    return " ".join(map(quote, cmds))


async def call(prog: str, *args: str, stdin: Optional[bytes] = None) -> int:
    proc = await create_subprocess_exec(
        prog,
        *args,
        stdin=PIPE if stdin else DEVNULL,
    )
    try:
        await proc.communicate(stdin)
        return await proc.wait()
    finally:
        with suppress(ProcessLookupError):
            proc.kill()
        await proc.wait()


async def run_in_executor(f: Callable[..., _T], *args: Any, **kwargs: Any) -> _T:
    fn = partial(f, *args, **kwargs)
    return await get_event_loop().run_in_executor(None, fn)
