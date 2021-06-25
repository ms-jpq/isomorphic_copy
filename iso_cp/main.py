from argparse import ArgumentParser, Namespace
from itertools import chain
from os import environ, pathsep
from pathlib import Path
from sys import stderr
from typing import Sequence, Tuple

from .consts import BIN
from .copy import copy
from .local_daemon import l_daemon
from .paste import paste
from .remote_daemon import r_daemon
from .shared import join


def _path_mask() -> None:
    paths = (path for path in environ["PATH"].split(pathsep) if path != str(BIN))
    environ["PATH"] = pathsep.join(paths)


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


def _parse_args() -> Tuple[Namespace, Sequence[str]]:
    parser = ArgumentParser()
    parser.add_argument("name")
    return parser.parse_known_args()


async def main() -> None:
    _path_mask()
    ns, args = _parse_args()
    name = Path(ns.name).name
    local = "ISOCP_USE_FILE" in environ

    if name in {"cssh", "cdocker"}:
        await l_daemon(local, name=name, args=args)
    elif name == "csshd":
        await r_daemon()
    elif _is_paste(name, args=args):
        await paste(local, args=args)
    elif _is_copy(name, args=args):
        await copy(local, args=args, data=None)
    else:
        sh = join(chain((name,), args))
        print(f"Unknown -- ", sh, file=stderr)
        exit(1)

