from asyncio import all_tasks, gather, get_event_loop

from .main import main

loop = None
try:
    loop = get_event_loop()
    try:
        code = loop.run_until_complete(main())
    except KeyboardInterrupt:
        exit(130)
    else:
        exit(code)
finally:
    if loop:
        try:
            tasks = all_tasks()
            for task in tasks:
                task.cancel()
            loop.run_until_complete(gather(*tasks, return_exceptions=True))
        finally:
            loop.close()
