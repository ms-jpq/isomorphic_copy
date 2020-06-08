#!/usr/bin/env python3

from os import environ, getcwd, unlink
from os.path import basename, dirname, join, relpath
from shutil import which
from socket import AF_UNIX, SOCK_STREAM, socket
from socketserver import BaseRequestHandler, UnixStreamServer
from subprocess import PIPE, Popen, run
from sys import argv, stderr, stdin, stdout
from time import sleep
from typing import List


#################### ########### ####################
#################### INIT Region ####################
#################### ########### ####################

__dir__ = dirname(__file__)


def path_mask() -> None:
  paths = (path
           for path in environ["PATH"].split(":")
           if path != __dir__)
  environ["PATH"] = ":".join(paths)


def socket_path() -> str:
  runtime_dir = environ.get(
      "XDG_RUNTIME_DIR", join(environ["HOME"], ".ssh"))
  return join(runtime_dir, "copy_socket")


#################### ########### ####################
#################### Copy Region ####################
#################### ########### ####################


def cp(data: bytes) -> None:
  if environ.get("TMUX"):
    run(["tmux", "load-buffer", "-"], input=data)

  if which("pbcopy"):
    run(["pbcopy"], input=data)
  elif which("wl-copy"):
    run(["wl-copy"], input=data)
  elif which("xclip"):
    run(["xclip"], input=data)


def rcp(data: bytes) -> None:
  path = socket_path()
  with socket(AF_UNIX, SOCK_STREAM) as sock:
    sock.connect(path)
    sock.sendall(data)
    sock.sendall(b'\0\n')


def cp_data(data: bytes) -> None:
  cp(data)
  if environ.get("SSH_TTY"):
    rcp(data)


def copy() -> None:
  data: bytes = stdin.read().strip("\n").encode()
  cp_data(data)


#################### ############ ####################
#################### Paste Region ####################
#################### ############ ####################


def paste() -> None:
  if which("pbpaste"):
    run(["pbpaste"])
  elif which("wl-paste"):
    run(["wl-paste"])
  elif which("xclip"):
    run(["xclip", "-out"])
  elif environ.get("TMUX"):
    run(["tmux", "save-buffer", "-"])
  else:
    print("⚠️ No clipboard integration ⚠️", file=stderr)
    exit(1)


#################### ########### ####################
#################### CSSH Region ####################
#################### ########### ####################


def cssh_prog() -> str:
  home = environ["HOME"]
  canonical = join(__dir__, "csshd")

  if canonical.startswith(home):
    prog = relpath(canonical, home)
    return f"$HOME/{prog}"
  else:
    return canonical


def cssh_run(args: List[str]) -> None:
  prog = cssh_prog()
  process: Popen = Popen(
      ["ssh", *args, prog],
      stdout=PIPE,
      stderr=PIPE)

  buf = bytearray()

  while True:
    code = process.poll()
    if code:
      print(f"ssh exited - {code}", file=stderr)
      print(process.stderr.read().decode(), file=stderr)
      return

    line: bytes = process.stdout.readline()
    for b in line:
      if b == 0:
        cp_data(buf)
        buf.clear()
        break
      else:
        buf.append(b)


def cssh() -> None:
  while True:
    cssh_run(argv[1:])
    sleep(1)
    print("\a")


#################### ############ ####################
#################### CSSHD Region ####################
#################### ############ ####################

def clean_socket(path: str) -> None:
  try:
    unlink(path)
  except IOError:
    pass


def csshd() -> None:
  class Handler(BaseRequestHandler):
    def handle(self) -> None:
      with self.request.makefile() as fd:
        data: str = fd.read()
        stdout.write(data)
        stdout.flush()

  path = socket_path()
  clean_socket(path)
  with UnixStreamServer(path, Handler) as srv:
    srv.serve_forever()


#################### ########### ####################
#################### Main Region ####################
#################### ########### ####################


def is_copy(name: str, args: List[str]) -> bool:
  if name in {"c", "pbcopy", "wl-copy"}:
    return True
  elif name == "xclip" and set(args).isdisjoint({"-o", "-out"}):
    return True
  else:
    return False


def is_paste(name: str, args: List[str]) -> bool:
  if name in {"p", "pbpaste", "wl-paste"}:
    return True
  elif name == "xclip" and not set(args).isdisjoint({"-o", "-out"}):
    return True
  else:
    return False


def main() -> None:
  path_mask()
  name = basename(argv[0])

  if name == "cssh":
    cssh()
  elif name == "csshd":
    csshd()
  elif is_paste(name, argv[1:]):
    paste()
  elif is_copy(name, argv[1:]):
    copy()
  else:
    print(f"Unknown -- {name} {' '.join(argv[1:])}", file=stderr)
    exit(1)


try:
  main()
except KeyboardInterrupt:
  pass
