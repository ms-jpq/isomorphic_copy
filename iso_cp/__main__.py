from asyncio import get_event_loop

from .main import main

loop = None
try:
    loop = get_event_loop()
    loop.run_until_complete(main())
except KeyboardInterrupt:
    exit(130)
finally:
    if loop:
        loop.close()

