import sys
from asyncio import get_event_loop
from sys import exit
from typing import Awaitable, TypeVar

from iso_cp.main import main

T = TypeVar("T")

if sys.version_info > (3, 7):
    from asyncio import run
else:

    def run(co: Awaitable[T]) -> T:
        loop = get_event_loop()
        try:
            return loop.run_until_complete(co)
        finally:
            try:
                loop.run_until_complete(loop.shutdown_asyncgens())
            finally:
                loop.close()


try:
    code = run(main())
except KeyboardInterrupt:
    exit(130)
else:
    exit(code)
