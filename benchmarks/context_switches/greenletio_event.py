import asyncio
import time
from greenletio import async_
from greenletio.green.threading import Event

CONTEXT_SWITCHES = 1000000


@async_
def run():
    wait_event = Event()
    wait_event.set()
    counter = 0
    while counter <= CONTEXT_SWITCHES:
        wait_event.wait()
        wait_event.clear()
        counter += 1
        wait_event.set()


async def main():
    now = time.perf_counter()
    await run()
    print('%f' % (time.perf_counter() - now))


asyncio.run(main())
