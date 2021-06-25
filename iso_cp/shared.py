from asyncio.subprocess import PIPE, create_subprocess_exec
from shlex import quote
from typing import Iterable, Optional, cast


def join(cmds: Iterable[str]) -> str:
    return " ".join(map(quote, cmds))


async def call(prog: str, *args: str, stdin: Optional[bytes] = None) -> int:
    proc = await create_subprocess_exec(prog, *args, stdin=PIPE)
    await proc.communicate(stdin)
    return cast(int, proc.returncode)

