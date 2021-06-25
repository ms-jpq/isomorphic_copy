from asyncio.subprocess import PIPE, create_subprocess_exec
from typing import Optional, Iterable

from shlex import quote

def join(cmds: Iterable[str]) -> str:
    return " ".join(map(quote, cmds))


async def call(prog: str, *args: str, stdin: Optional[bytes] = None) -> None:
    proc = await create_subprocess_exec(prog, *args, stdin=PIPE)
    await proc.communicate(stdin)
    if proc.returncode != 0:
        exit(proc.returncode)

