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
                    gl.switch(*args, **kwargs)
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


async def _run_greenlet_in_aio(gl, args=None, kwargs=None, coro=None):
    gl._greenletio_running = True
    if coro is None:
        coro = gl.switch(*args, **kwargs)
    while gl and coro != ():
        ret = None
        try:
            ret = await coro
        except:  # noqa: E722
            coro = gl.throw(*sys.exc_info())
        else:
            coro = gl.switch(ret)
    del gl._greenletio_running
    return coro


def async_(fn):
    @functools.wraps(fn)
    def decorator(*args, **kwargs):
        if not bridge.running and not bridge.starting:
            bridge.start()
        return _run_greenlet_in_aio(greenlet(fn), args=args, kwargs=kwargs)

    return decorator


def await_(coro_or_fn):
    if asyncio.iscoroutine(coro_or_fn) or asyncio.isfuture(coro_or_fn):
        # we were given an awaitable --> await it
        if not bridge.running and not bridge.starting:
            bridge.start()

        gl = getcurrent()
        if not hasattr(gl, '_greenletio_running'):
            bridge.loop.create_task(_run_greenlet_in_aio(gl, coro=coro_or_fn))
            return bridge.switch()
        else:
            return bridge.bridge_greenlet.switch(coro_or_fn)
    else:
        # assume decorator usage
        @functools.wraps(coro_or_fn)
        def decorator(*args, **kwargs):
            return await_(coro_or_fn(*args, **kwargs))

        return decorator


def spawn(fn, *args, **kwargs):
    if not bridge.running and not bridge.starting:
        bridge.start()

    def _fn(*args, **kwargs):
        fn(*args, **kwargs)
        getcurrent().parent = bridge.bridge_greenlet

    gl = greenlet(_fn)
    bridge.schedule(gl, *args, **kwargs)
    return gl
