from pathlib import Path

NUL = b"\0"
TIME_FMT = "%Y-%m-%d %H:%M:%S"

_TOP_LV = Path(__file__).resolve().parent.parent
TMP = _TOP_LV / "tmp"


BIN = _TOP_LV / "bin"
EXEC = TMP / "python"
SOCKET_PATH = TMP / "cp.socket"
WRITE_PATH = TMP / "clipboard.txt"
