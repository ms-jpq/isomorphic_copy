from pathlib import Path

NUL = b"\0"
TIME_FMT = "%Y-%m-%d %H:%M:%S"

_TOP_LV = Path(__file__).resolve().parent.parent
_TMP = _TOP_LV / "tmp"


BIN = _TOP_LV / "bin"
EXEC = _TMP / "python"
SOCKET_PATH = _TMP / "cp.socket"
WRITE_PATH = _TMP / "clipboard.txt"
