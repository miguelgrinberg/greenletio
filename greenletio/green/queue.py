import asyncio
from collections import deque
from greenletio.core import await_
from greenletio.green import threading
from greenletio.patcher import copy_globals
import queue as _original_queue_

copy_globals(_original_queue_, globals())
Empty = asyncio.QueueEmpty
Full = asyncio.QueueFull


class _QueueMixin:
    def put(self, item, block=True, timeout=None):
        if not block:
            self.put_nowait(item)
        elif timeout is None:
            await_(super().put(item))
        else:
            await_(asyncio.wait_for(super().put(item), timeout))

    def get(self, block=True, timeout=None):
        if not block:
            return self.get_nowait()
        if timeout is None:
            return await_(super().get())
        else:
            try:
                return await_(asyncio.wait_for(super().get(), timeout))
            except asyncio.TimeoutError:
                raise Empty()

    def join(self):
        await_(super().join())


class Queue(_QueueMixin, asyncio.Queue):
    pass


class LifoQueue(_QueueMixin, asyncio.LifoQueue):
    pass


class PriorityQueue(_QueueMixin, asyncio.PriorityQueue):
    pass


class SimpleQueue:
    def __init__(self):
        self._queue = deque()
        self._count = threading.Semaphore(0)

    def put(self, item, block=True, timeout=None):
        self._queue.append(item)
        self._count.release()

    def get(self, block=True, timeout=None):
        if not self._count.acquire(block, timeout):
            raise Empty
        return self._queue.popleft()

    def put_nowait(self, item):
        return self.put(item, block=False)

    def get_nowait(self):
        return self.get(block=False)

    def empty(self):
        return len(self._queue) == 0

    def qsize(self):
        return len(self._queue)
