#!/usr/bin/env python3

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
from os import environ, linesep, pathsep
from pathlib import Path
from shutil import which
from sys import argv, stderr, stdin
from typing import Optional, Sequence, Tuple, cast

#################### ########### ####################
#################### INIT Region ####################
#################### ########### ####################

_NUL = b"\0"

_DIR = Path(__file__).resolve().parent
_BIN = _DIR / "bin"
_TMP = _DIR / "tmp"
_SOCKET_PATH = _TMP / "cp.socket"
_WRITE_PATH = _TMP / "clipboard.txt"


_NAME = Path(argv[1]).name
_ARGS = argv[2:]
_LOCAL_WRITE = environ.get("ISOCP_USE_FILE") is not None


def _path_mask() -> None:
    paths = (path for path in environ["PATH"].split(pathsep) if path != _BIN)
    environ["PATH"] = pathsep.join(paths)


async def _call(prog: str, *args: str, stdin: bytes = None) -> None:
    proc = await create_subprocess_exec(prog, *args, stdin=PIPE)
    await proc.communicate(stdin)
    if proc.returncode != 0:
        exit(proc.returncode)


#################### ########### ####################
#################### Copy Region ####################
#################### ########### ####################


def _local_copy(data: bytes) -> None:
    _WRITE_PATH.write_bytes(data)


def _is_remote() -> bool:
    if "SSH_TTY" in environ:
        return True
    elif Path("/", ".dockerenv").exists():
        return True
    else:
        return False


async def _rcp(data: bytes) -> None:
    try:
        conn = await open_unix_connection(_SOCKET_PATH)
    except (FileNotFoundError, ConnectionRefusedError):
        pass
    else:
        _, writer = conn
        writer.write(data)
        writer.write(_NUL)
        await writer.drain()


async def _copy(text: Optional[bytes]) -> None:
    data: bytes = text or stdin.read().encode()
    tasks = []

    if _is_remote():
        tasks.append(_rcp(data))

    if environ.get("TMUX"):
        tasks.append(_call("tmux", "load-buffer", "-", stdin=data))

    if which("pbcopy"):
        tasks.append(_call("pbcopy", stdin=data))

    elif environ.get("WAYLAND_DISPLAY") and which("wl-copy"):
        tasks.append(_call("wl-copy", stdin=data))

    elif environ.get("DISPLAY") and which("xclip"):
        tasks.append(_call("xclip", *_ARGS, "-selection", "clipboard", stdin=data))
        tasks.append(_call("xclip", *_ARGS, "-selection", "primary", stdin=data))

    elif _LOCAL_WRITE:
        _local_copy(data)

    await gather(*tasks)


#################### ############ ####################
#################### Paste Region ####################
#################### ############ ####################


def _local_paste() -> None:
    try:
        text = _WRITE_PATH.read_text()
        print(text, end="", flush=True)
    except OSError:
        pass


async def _paste() -> None:
    if which("pbpaste"):
        await _call("pbpaste")

    elif environ.get("WAYLAND_DISPLAY") and which("wl-paste"):
        await _call("wl-paste")

    elif environ.get("DISPLAY") and which("xclip"):
        args = (*_ARGS, "-out") if set(_ARGS).isdisjoint({"-o", "-out"}) else _ARGS
        await _call("xclip", *args, "-selection", "clipboard")
        # await call("xclip", *args, "-selection", "primary")

    elif environ.get("TMUX"):
        await _call("tmux", "save-buffer", "-")

    elif _LOCAL_WRITE:
        _local_paste()

    else:
        print(
            "⚠️  No system clipboard detected ⚠️",
            linesep * 2,
            "export ISOCP_USE_FILE=1 to use temp file",
            file=stderr,
            sep="",
        )
        exit(1)


#################### ########### ####################
#################### CSSH Region ####################
#################### ########### ####################


def _cssh_cmd() -> Tuple[Sequence[str], Sequence[str]]:
    lookup = {
        "cssh": (("ssh",), ()),
        "cdocker": (("docker", "exec"), ()),
    }
    return lookup[_NAME]


def _cssh_prog() -> str:
    canonical = _BIN / "csshd"

    try:
        rel_path = canonical.relative_to(Path.home())
    except ValueError:
        return str(canonical)
    else:
        return f"\"$HOME\"'{rel_path}'"


async def _cssh_run(args: Sequence[str]) -> None:
    prev, post = _cssh_cmd()
    prog = _cssh_prog()
    exe = (*prev, *args, *post, "sh", "-c", prog)
    proc = await create_subprocess_exec(*exe, stdin=DEVNULL, stdout=PIPE)
    stdout = cast(StreamReader, proc.stdout)

    print(f"Communicating via:", linesep, " ".join(exe), sep="")
    while True:
        code = proc.returncode
        if code:
            print(f"daemon exited - {code}", file=stderr)
            break
        else:
            try:
                data = await stdout.readuntil(_NUL)
            except IncompleteReadError:
                break
            else:
                time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(linesep, f"-- RECV -- {time}", linesep, sep="")
                await _copy(data[:-1])


async def _cssh() -> None:
    while True:
        await _cssh_run(_ARGS)
        print("\a", end="")
        await sleep(1)


#################### ############ ####################
#################### CSSHD Region ####################
#################### ############ ####################


async def _csshd() -> None:
    async def handler(reader: StreamReader, _: StreamWriter) -> None:
        data = await reader.readuntil(_NUL)
        print(data.decode(), end="", flush=True)

    server: AbstractServer = await start_unix_server(handler, _SOCKET_PATH)
    await server.wait_closed()


#################### ########### ####################
#################### Main Region ####################
#################### ########### ####################


def _is_copy() -> bool:
    if _NAME in {"c", "pbcopy", "wl-copy"}:
        return True
    elif _NAME == "xclip" and {*_ARGS}.isdisjoint({"-o", "-out"}):
        return True
    else:
        return False


def _is_paste() -> bool:
    if _NAME in {"p", "pbpaste", "wl-paste"}:
        return True
    elif _NAME == "xclip" and not {*_ARGS}.isdisjoint({"-o", "-out"}):
        return True
    else:
        return False


async def main() -> None:
    _path_mask()

    if _NAME in {"cssh", "cdocker"}:
        await _cssh()
    elif _NAME == "csshd":
        await _csshd()
    elif _is_paste():
        await _paste()
    elif _is_copy():
        await _copy(None)
    else:
        print(f"Unknown -- {_NAME} {' '.join(_ARGS)}", file=stderr)
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
