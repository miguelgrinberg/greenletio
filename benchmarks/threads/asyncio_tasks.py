import asyncio
import random
import time


async def t():
    for i in range(1000):
        await asyncio.sleep(random.random() / 1000)


async def run():
    tasks = [asyncio.create_task(t()) for i in range(300)]
    await asyncio.gather(*tasks)


def main():
    now = time.perf_counter()
    asyncio.run(run())
    print('%f' % (time.perf_counter() - now))


main()
