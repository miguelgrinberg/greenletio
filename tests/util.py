import asyncio
import sys


def run_coro(coro):
    if sys.platform == 'win32':
        loop = asyncio.SelectorEventLoop()
    else:
        loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)
