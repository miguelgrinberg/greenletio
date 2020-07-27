import asyncio
import atexit
from collections import deque
import functools
import sys
from greenlet import greenlet, getcurrent


class GreenletBridge:
    def __init__(self):
        self.reset()

    def reset(self):
        self.starting = False
        self.running = False
        self.stopping = False
        self.loop = None
        self.bridge_greenlet = None
        self.wait_event = None
        self.scheduled = deque()

    def schedule(self, gl, *args, **kwargs):
        self.scheduled.append((gl, args, kwargs))
        if self.wait_event:
            self.wait_event.set()

    def run(self):
        async def async_run():
            self.starting = False
            self.stopping = False
            self.running = True
            while not self.stopping:
                self.wait_event.clear()
                while self.scheduled:
                    gl, args, kwargs = self.scheduled.popleft()
                    gl.switch(*args, **kwargs)
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
            self.bridge_greenlet.parent = getcurrent()
            self.bridge_greenlet.switch()

    def switch(self):
        if self.bridge_greenlet is None:
            self.bridge_greenlet = greenlet(self.run)
        if self.wait_event:
            self.wait_event.set()
        return self.bridge_greenlet.switch()


bridge = GreenletBridge()


def async_(fn):
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
    if asyncio.iscoroutine(coro_or_fn):
        # we were given a coroutine --> await it
        if not bridge.running and not bridge.starting:
            bridge.start()

        async def run_in_aio(gl):
            ret = None
            exc_info = None
            try:
                ret = await coro_or_fn
            except:  # noqa: E722
                exc_info = sys.exc_info()
            bridge.schedule(gl, (ret, exc_info))

        bridge.loop.create_task(run_in_aio(getcurrent()))
        ret, exc_info = bridge.switch()
        if exc_info:
            raise exc_info[0].with_traceback(exc_info[1], exc_info[2])
        return ret
    else:
        # assume decorator usage
        @functools.wraps(coro_or_fn)
        def decorator(*args, **kwargs):
            return await_(coro_or_fn(*args, **kwargs))

        return decorator


def spawn(fn, *args, **kwargs):
    if not bridge.running and not bridge.starting:
        bridge.start()
    gl = greenlet(fn)
    gl.parent = bridge.bridge_greenlet
    bridge.schedule(gl, *args, **kwargs)
    return gl
