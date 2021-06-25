from asyncio import get_event_loop

from .main import main

loop = None
try:
    loop = get_event_loop()
    code = loop.run_until_complete(main())
except KeyboardInterrupt:
    exit(130)
else:
    exit(code)
finally:
    if loop:
        loop.close()

