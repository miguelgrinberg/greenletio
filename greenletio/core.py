import asyncio
import functools
from greenlet import greenlet, getcurrent


class GreenletBridge:
    def __init__(self):
        self.running = False
        self.stopping = False
        self.bridge_greenlet = None
        self.wait_event = None
        self.scheduled = []

    def schedule(self, gl, *args, **kwargs):
        self.scheduled.append((gl, args, kwargs))
        if self.wait_event:
            self.wait_event.set()

    def run(self):
        async def async_run():
            self.running = True
            while not self.stopping:
                self.wait_event.clear()
                while self.scheduled:
                    gl, args, kwargs = self.scheduled.pop(0)
                    gl.switch(*args, **kwargs)
                await self.wait_event.wait()
            self.running = False

        # get the asyncio loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if not self.running:
            self.wait_event = asyncio.Event()
            if not loop.is_running():
                # neither the loop nor the bridge are running
                # start a loop with the bridge task
                loop.run_until_complete(async_run())
            else:
                # the loop is already running, but the bridge isn't
                # start the bridge as a task
                loop.create_task(async_run())
        else:
            # both the loop and the bridge are running
            # awake the bridge
            self.wait_event.set()

    def start(self):
        if not self.running:
            self.schedule(getcurrent())
            self.switch()

    def stop(self):
        self.stopping = True
        self.wait_event.set()

    def switch(self):
        if self.bridge_greenlet is None:
            self.bridge_greenlet = greenlet(self.run)
        elif self.wait_event:
            self.wait_event.set()
        return self.bridge_greenlet.switch()


bridge = GreenletBridge()


def async_(fn):
    @functools.wraps(fn)
    def decorator(*args, **kwargs):
        if not bridge.running:
            bridge.start()

        async def coro(fn, *args, **kwargs):
            future = asyncio.Future()

            def _gl():
                future.set_result(fn(*args, **kwargs))

            bridge.schedule(greenlet(_gl))
            return await future

        return coro(fn, *args, **kwargs)

    return decorator


def await_(coro_or_fn):
    if asyncio.iscoroutine(coro_or_fn):
        # we were given a coroutine --> await it
        if not bridge.running:
            bridge.start()

        async def run_in_aio(gl):
            ret = None
            error = None
            try:
                ret = await coro_or_fn
            except Exception as exc:
                error = exc
            bridge.schedule(gl, (ret, error))

        asyncio.create_task(run_in_aio(getcurrent()))
        ret, error = bridge.switch()
        if error:
            raise error
        return ret
    else:
        # assume decorator usage
        @functools.wraps(coro_or_fn)
        def decorator(*args, **kwargs):
            return await_(coro_or_fn(*args, **kwargs))

        return decorator
