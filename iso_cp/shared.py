from asyncio.subprocess import DEVNULL, PIPE, create_subprocess_exec
from contextlib import suppress
from shlex import quote
from typing import Iterable, Optional, cast


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
    finally:
        with suppress(ProcessLookupError):
            await proc.wait()

    return cast(int, proc.returncode)
