import asyncio
import random
from greenletio import await_


def main():
    for i in range(10):
        await_(asyncio.sleep(random.random()))
        print(i)


main()
