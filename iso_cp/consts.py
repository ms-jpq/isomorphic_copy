from pathlib import Path

NUL = b"\0"
LIMIT = 2**32
TIME_FMT = "%Y-%m-%d %H:%M:%S"

TITLE = "ISO-CP"
TOP_LV = Path(__file__).resolve().parent.parent
TMP = TOP_LV / "tmp"


BIN = TOP_LV / "bin"
EXEC = TMP / "python"

SOCKET_PATH = TMP / "cp.socket"
WRITE_PATH = TMP / "clipboard.txt"

L_UID_PATH = TMP / "l_uid"
R_UID_PATH = TMP / "r_uid"
