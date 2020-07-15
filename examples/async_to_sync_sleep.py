import asyncio
import random
from greenletio import async_, await_


@async_
def sleep(delay):
    await_(asyncio.sleep(delay))


async def main():
    for i in range(10):
        await sleep(random.random())
        print(i)


asyncio.run(main())
