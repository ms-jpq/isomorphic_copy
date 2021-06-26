from argparse import ArgumentParser, Namespace
from asyncio import create_task, sleep
from itertools import chain
from locale import strxfrm
from os import environ, getpid, getppid, kill, pathsep, readlink
from pathlib import Path
from signal import SIGKILL
from sys import executable
from typing import Sequence, Tuple

from .consts import BIN, EXEC
from .copy import copy
from .local_daemon import l_daemon
from .paste import paste
from .remote_daemon import r_daemon


async def _suicide() -> None:
    while True:
        if getppid() == 1:
            kill(getpid(), SIGKILL)
        await sleep(1)


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

    create_task(_suicide())
    if name in {"cssh", "cdocker"}:
        return await l_daemon(local, name=name, args=args)
    elif name == "csshd":
        return await r_daemon()
    elif _is_paste(name, args=args):
        return await paste(local, args=args)
    elif _is_copy(name, args=args):
        return await copy(local, args=args, data=None)
    else:
        assert False

