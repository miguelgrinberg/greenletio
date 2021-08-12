import asyncio
import atexit
from collections import deque
import functools
import sys
from greenlet import greenlet, getcurrent


class GreenletBridge:
    def __init__(self):
        self.reset()
        self.wait_event = None

    def reset(self):
        self.starting = False
        self.running = False
        self.stopping = False
        self.loop = None
        self.bridge_greenlet = None
        self.scheduled = deque()
        self.pending_io = object()

    def schedule(self, gl, *args, **kwargs):
        self.scheduled.append((gl, args, kwargs))
        if self.wait_event:
            self.wait_event.set()

    def run(self):
        async def async_run():
            if self.bridge_greenlet != getcurrent():
                self.bridge_greenlet = getcurrent()
            self.starting = False
            self.stopping = False
            self.running = True
            while not self.stopping or self.scheduled:
                self.wait_event.clear()
                while self.scheduled:
                    gl, args, kwargs = self.scheduled.popleft()
                    self.loop.create_task(_run_greenlet_in_aio(
                        gl, args=args, kwargs=kwargs))
                if self.stopping:  # pragma: no cover
                    break
                await self.wait_event.wait()
            self.running = False

        # get the asyncio loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:  # pragma: no cover
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        self.loop = loop
        self.wait_event = asyncio.Event()
        if not loop.is_running():
            # neither the loop nor the bridge are running
            # start a loop with the bridge task
            loop.run_until_complete(async_run())
        else:
            # the loop is already running, but the bridge isn't
            # start the bridge as a task
            loop.create_task(async_run())

    def start(self):
        assert not self.running and not self.starting
        atexit.register(self.stop)
        self.reset()
        self.starting = True
        self.schedule(getcurrent())
        self.switch()

    def stop(self):
        if self.running:
            self.stopping = True
            self.wait_event.set()
            if self.bridge_greenlet != getcurrent():
                self.bridge_greenlet.parent = getcurrent()
                while not self.bridge_greenlet.dead:  # pragma: no cover
                    self.bridge_greenlet.switch()

    def switch(self):
        if self.bridge_greenlet is None:
            self.bridge_greenlet = greenlet(self.run)
        if self.wait_event:
            self.wait_event.set()
        return self.bridge_greenlet.switch()


bridge = GreenletBridge()


async def _run_greenlet_in_aio(gl, args=None, kwargs=None):
    # run the function until one of two things happen:
    # - await_() is called, which would switch back to us with the awaitable
    # - another blocking condition is issued, such as wait for I/O or sleep,
    #   which would return an empty tuple
    coro = gl.switch(*args, **kwargs)

    # continue to run the greenlet for as long as it does not end and keeps
    # returning awaitables
    while gl and coro != ():
        ret = None
        try:
            ret = await coro
        except:  # noqa: E722
            coro = gl.throw(*sys.exc_info())
        else:
            coro = gl.switch(ret)
    return coro


def async_(fn):
    """Convert a standard function to an async function that can be awaited.

    This function creates an async wrapper for a standard function, allowing
    callers to invoke the function as an awaitable. Example::

        def fn():
            pass

        async def main():
            await async_(fn)

    It is also possible to use this function as a decorator::

        @async_
        def fn():
            pass

        async def main():
            await fn()

    :param fn: the standard function to convert to async.
    """
    @functools.wraps(fn)
    def decorator(*args, **kwargs):
        if not bridge.running and not bridge.starting:
            bridge.start()

        async def coro(fn, *args, **kwargs):
            future = asyncio.Future()

            def gl(future, fn, *args, **kwargs):
                try:
                    future.set_result(fn(*args, **kwargs))
                except:  # noqa: E722
                    future.set_exception(sys.exc_info()[1])

            bridge.schedule(greenlet(gl), future, fn, *args, **kwargs)
            return await future

        return coro(fn, *args, **kwargs)

    return decorator


def await_(coro_or_fn):
    """Wait for an async function to complete in a standard function, without
    blocking the asyncio loop.

    This function can be used in two ways. First, as a replacement to the
    ``await`` keyword in a standard function::

        def func():
            await_(asyncio.sleep(1))

    Second, as a decorator to an async function, so that the function
    can be called as a standard function while still not blocking the asyncio
    loop::

        @await_
        async def func():
            await asyncio.sleep(1)

        def main():
            func()

    :param coro_or_fn: The coroutine or future to await, or when used as a
                       decorator, the async function to decorate.
    """
    if asyncio.iscoroutine(coro_or_fn) or asyncio.isfuture(coro_or_fn):
        # we were given an awaitable --> await it
        if not bridge.running and not bridge.starting:
            bridge.start()
        if bridge.bridge_greenlet == getcurrent():
            raise RuntimeError('Cannot use await_ in asyncio thread')

        return bridge.bridge_greenlet.switch(coro_or_fn)
    else:
        # assume decorator usage
        @functools.wraps(coro_or_fn)
        def decorator(*args, **kwargs):
            return await_(coro_or_fn(*args, **kwargs))

        return decorator


def spawn(fn, *args, **kwargs):
    """Run a standard function asynchronously in a greenlet.

    This function is mostly used internally, so in general it is not needed by
    applications. The main purpose is to be able to use the
    :func:`greenletio.await_` function.

    :param fn: the function to run.
    :param args: positional function arguments.
    :param kwargs: keyboard function arguments.
    """
    if not bridge.running and not bridge.starting:
        bridge.start()

    def _fn(*args, **kwargs):
        getcurrent().parent = bridge.bridge_greenlet
        fn(*args, **kwargs)

    gl = greenlet(_fn)
    bridge.schedule(gl, *args, **kwargs)
    return gl
