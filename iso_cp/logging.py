from contextlib import contextmanager
from logging import INFO, StreamHandler, getLogger
from typing import Iterator

log = getLogger(__name__)
log.addHandler(StreamHandler())
log.setLevel(INFO)


@contextmanager
def log_exc() -> Iterator[None]:
    try:
        yield None
    except Exception as e:
        log.exception("%s", e)
