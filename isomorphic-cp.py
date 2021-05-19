#!/usr/bin/env python3

from argparse import ArgumentParser, Namespace
from asyncio import (
    IncompleteReadError,
    StreamReader,
    StreamWriter,
    gather,
    get_event_loop,
    open_unix_connection,
    sleep,
    start_unix_server,
)
from asyncio.events import AbstractServer
from asyncio.subprocess import DEVNULL, PIPE, create_subprocess_exec
from datetime import datetime
from itertools import chain
from os import environ, linesep, pathsep, sep
from pathlib import Path
from shlex import quote
from shutil import which
from sys import stderr, stdin, stdout
from typing import Iterable, Optional, Sequence, Tuple, cast

#################### ########### ####################
#################### INIT Region ####################
#################### ########### ####################

_NUL = b"\0"
_TIME_FMT = "%Y-%m-%d %H:%M:%S"

_DIR = Path(__file__).resolve().parent
_BIN = _DIR / "bin"
_TMP = _DIR / "tmp"
_SOCKET_PATH = _TMP / "cp.socket"
_WRITE_PATH = _TMP / "clipboard.txt"


_LOCAL_WRITE = "ISOCP_USE_FILE" in environ


def _path_mask() -> None:
    paths = (path for path in environ["PATH"].split(pathsep) if path != str(_BIN))
    environ["PATH"] = pathsep.join(paths)


def _join(cmds: Iterable[str]) -> str:
    return " ".join(map(quote, cmds))


async def _call(prog: str, *args: str, stdin: Optional[bytes] = None) -> None:
    proc = await create_subprocess_exec(prog, *args, stdin=PIPE)
    await proc.communicate(stdin)
    if proc.returncode != 0:
        exit(proc.returncode)


#################### ########### ####################
#################### Copy Region ####################
#################### ########### ####################


def _is_remote() -> bool:
    if "SSH_TTY" in environ:
        return True
    elif Path(sep, ".dockerenv").exists():
        return True
    else:
        return False


async def _rcp(data: bytes) -> None:
    try:
        conn = await open_unix_connection(str(_SOCKET_PATH))
    except (FileNotFoundError, ConnectionRefusedError):
        pass
    else:
        _, writer = conn
        writer.write(data)
        writer.write(_NUL)
        await writer.drain()


async def _copy(args: Sequence[str], data: Optional[bytes]) -> None:
    data = data or stdin.read().encode()
    tasks = []

    if _is_remote():
        tasks.append(_rcp(data))

    if "TMUX" in environ:
        tasks.append(_call("tmux", "load-buffer", "-", stdin=data))

    if which("pbcopy"):
        tasks.append(_call("pbcopy", stdin=data))

    if which("wl-copy") and "WAYLAND_DISPLAY" in environ:
        tasks.append(_call("wl-copy", stdin=data))

    elif which("xclip") and "DISPLAY" in environ:
        tasks.append(_call("xclip", *args, "-selection", "clipboard", stdin=data))
        tasks.append(_call("xclip", *args, "-selection", "primary", stdin=data))

    elif _LOCAL_WRITE:
        _WRITE_PATH.write_bytes(data)

    await gather(*tasks)


#################### ############ ####################
#################### Paste Region ####################
#################### ############ ####################


async def _paste(args: Sequence[str]) -> None:
    if which("pbpaste"):
        await _call("pbpaste")

    elif which("wl-copy") and "WAYLAND_DISPLAY" in environ:
        await _call("wl-paste")

    elif which("xclip") and "DISPLAY" in environ:
        xargs = chain(args, ("-out",)) if {*args}.isdisjoint({"-o", "-out"}) else args
        await _call("xclip", *xargs, "-selection", "clipboard")
        # await call("xclip", *args, "-selection", "primary")

    elif "TMUX" in environ:
        await _call("tmux", "save-buffer", "-")

    elif _LOCAL_WRITE:
        if _WRITE_PATH.exists():
            data = _WRITE_PATH.read_bytes()
            stdout.buffer.write(data)
            stdout.buffer.flush()

    else:
        print(
            "⚠️  No system clipboard detected ⚠️",
            "export ISOCP_USE_FILE=1 to use temp file",
            sep=linesep * 2,
            file=stderr,
        )
        exit(1)


#################### ########### ####################
#################### CSSH Region ####################
#################### ########### ####################


def _cssh_cmd(name: str) -> Tuple[Sequence[str], Sequence[str]]:
    lookup = {
        "cssh": (("ssh",), ()),
        "cdocker": (("docker", "exec"), ()),
    }
    return lookup[name]


def _cssh_prog() -> str:
    canonical = _BIN / "csshd"

    try:
        rel_path = canonical.relative_to(Path.home())
    except ValueError:
        return quote(str(canonical))
    else:
        return '"$HOME"' + quote(str(Path(sep, rel_path)))


async def _cssh_run(name: str, args: Sequence[str]) -> None:
    prev, post = _cssh_cmd(name)
    prog = _cssh_prog()
    exe = (*prev, *args, *post, "sh", "-c", prog)
    proc = await create_subprocess_exec(*exe, stdin=DEVNULL, stdout=PIPE)
    stdout = cast(StreamReader, proc.stdout)

    sh = _join(exe)
    print(f"Establishing link via:", sh, sep=linesep, file=stderr)

    while True:
        code = proc.returncode
        if code:
            print(f"Exited - ", code, file=stderr)
            break
        else:
            try:
                data = await stdout.readuntil(_NUL)
            except IncompleteReadError:
                break
            else:
                time = datetime.now().strftime(_TIME_FMT)
                await _copy(args, data=data[:-1])
                print(
                    linesep,
                    f"-- RECV -- {time}",
                    linesep,
                    sep="",
                    file=stderr,
                )


async def _cssh(name: str, args: Sequence[str]) -> None:
    while True:
        await _cssh_run(name, args=args)
        print("\a", end="", file=stderr)
        await sleep(1)


#################### ############ ####################
#################### CSSHD Region ####################
#################### ############ ####################


async def _csshd() -> None:
    async def handler(reader: StreamReader, _: StreamWriter) -> None:
        data = await reader.readuntil(_NUL)
        stdout.buffer.write(data)
        stdout.buffer.flush()

    server: AbstractServer = await start_unix_server(handler, str(_SOCKET_PATH))
    await server.wait_closed()


#################### ########### ####################
#################### Main Region ####################
#################### ########### ####################


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

    if name in {"cssh", "cdocker"}:
        await _cssh(name, args=args)
    elif name == "csshd":
        await _csshd()
    elif _is_paste(name, args=args):
        await _paste(args)
    elif _is_copy(name, args=args):
        await _copy(args, data=None)
    else:
        sh = _join(chain((name,), args))
        print(f"Unknown -- ", sh, file=stderr)
        exit(1)


loop = None
try:
    loop = get_event_loop()
    loop.run_until_complete(main())
except KeyboardInterrupt:
    exit(130)
finally:
    if loop:
        loop.close()
