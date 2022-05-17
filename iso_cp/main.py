from argparse import ArgumentParser, Namespace
from asyncio import Future, ensure_future, sleep
from itertools import chain
from locale import strxfrm
from os import environ, getpid, getppid, kill, pathsep, readlink
from pathlib import Path
from signal import SIGTERM
from sys import executable, stdin
from typing import Any, Awaitable, Optional, Sequence, Tuple
from uuid import uuid4

from .consts import BIN, EXEC, L_UID_PATH, R_UID_PATH
from .copy import copy
from .local_daemon import l_daemon
from .logging import log_exc
from .paste import paste
from .remote_daemon import r_daemon
from .shared import run_in_executor, safe_write


def _suicide() -> None:
    kill(getpid(), SIGTERM)


async def _s1() -> None:
    ppid = getppid()
    while True:
        cppid = getppid()
        if cppid == 1 or cppid != ppid:
            _suicide()
        else:
            await sleep(1)


async def _s2(path: Path) -> None:
    b4 = uuid4().bytes

    def c1() -> None:
        safe_write(path, data=b4)

    await run_in_executor(c1)

    def c2() -> bytes:
        try:
            return path.read_bytes()
        except FileNotFoundError:
            return b""

    while True:
        b = await run_in_executor(c2)
        if b != b4:
            _suicide()
        await sleep(1)


class _Suicide:
    def __init__(self, s: Awaitable[None]) -> None:
        self._t: Optional[Future] = None
        self._s = s

    async def _suicide(self) -> None:
        with log_exc():
            await self._s

    async def __aenter__(self) -> None:
        with log_exc():
            self._t = ensure_future(self._suicide())
            await sleep(0)

    async def __aexit__(self, *_: Any) -> None:
        with log_exc():
            await sleep(0)
            if self._t:
                self._t.cancel()
                while not self._t.done():
                    await sleep(0)


def _path_mask() -> None:
    paths = (path for path in environ["PATH"].split(pathsep) if path != str(BIN))
    environ["PATH"] = pathsep.join(paths)


def _link() -> None:
    python = Path(executable).resolve()
    try:
        if Path(readlink(EXEC)) != python:
            EXEC.unlink()
            EXEC.symlink_to(python)
    except FileNotFoundError:
        EXEC.symlink_to(python)


def _is_copy(name: str, args: Sequence[str]) -> bool:
    if name in {"c", "pbcopy", "wl-copy"}:
        return True
    elif name == "xclip" and {*args}.isdisjoint({"-o", "-out"}):
        return True
    else:
        return False


def _is_paste(name: str, args: Sequence[str]) -> bool:
    if name in {"p", "pbpaste", "wl-paste"}:
        return True
    elif name == "xclip" and not {*args}.isdisjoint({"-o", "-out"}):
        return True
    else:
        return False


def _legal_names() -> Sequence[str]:
    paths = sorted(BIN.iterdir(), key=lambda p: tuple(map(strxfrm, p.parts)))
    names = tuple(chain((p.name for p in paths), map(str, paths)))
    return names


def _parse_args() -> Tuple[Namespace, Sequence[str]]:
    parser = ArgumentParser()
    parser.add_argument("name", choices=_legal_names())
    return parser.parse_known_args()


async def main() -> int:
    _path_mask()
    _link()

    ns, args = _parse_args()
    name = Path(ns.name).name
    local = "ISOCP_USE_FILE" in environ

    async with _Suicide(_s1()):
        if name in {"cssh", "cdocker"}:
            async with _Suicide(_s2(L_UID_PATH)):
                return await l_daemon(local, name=name, args=args)
        elif name == "csshd":
            async with _Suicide(_s2(R_UID_PATH)):
                return await r_daemon()
        elif _is_paste(name, args=args):
            return await paste(local, args=args)
        elif _is_copy(name, args=args):
            data = await run_in_executor(stdin.buffer.read)
            return await copy(local, args=args, data=data)
        else:
            assert False
