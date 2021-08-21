import asyncio
import time

CONTEXT_SWITCHES = 1000000


async def run():
    wait_event = asyncio.Event()
    wait_event.set()
    counter = 0
    while counter <= CONTEXT_SWITCHES:
        await wait_event.wait()
        wait_event.clear()
        counter += 1
        wait_event.set()


def main():
    now = time.perf_counter()
    asyncio.run(run())
    print('%f' % (time.perf_counter() - now))


main()
