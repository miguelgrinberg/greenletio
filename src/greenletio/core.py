import asyncio
import contextvars
import functools
import sys
from greenlet import greenlet, getcurrent


class GreenletBridge:
    stop_bridge = object()

    def __init__(self):
        self.bridge_greenlet = None

    def run(self):
        async def async_run():
            gl = getcurrent().parent
            coro = gl.switch()
            while gl and coro != self.stop_bridge:  # pragma: no branch
                try:
                    result = await coro
                except:  # noqa: E722
                    coro = gl.throw(*sys.exc_info())
                else:
                    coro = gl.switch(result)

        # get the asyncio loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:  # pragma: no cover
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        loop.run_until_complete(async_run())
        self.bridge_greenlet = None

    def start(self):
        if self.bridge_greenlet:
            return self.bridge_greenlet
        if asyncio.get_event_loop().is_running():
            # we shouldn't be here if a loop is already running!
            return getcurrent()

        self.bridge_greenlet = greenlet(self.run)
        self.bridge_greenlet.switch()
        return self.bridge_greenlet

    def stop(self):
        if self.bridge_greenlet:
            self.bridge_greenlet.switch(self.stop_bridge)
            self.bridge_greenlet = None


bridge = GreenletBridge()


def async_(fn=None, *, with_context=False):
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

    If you are using context variables, you can use the ``with_context`` option
    to ensure that the context is preserved when the function is called::

        @async_(with_context=True)
        def fn():
            pass

    :param fn: the standard function to convert to async.
    """
    if fn is None:
        return lambda fn: async_(fn, with_context=with_context)

    @functools.wraps(fn)
    async def decorator(*args, **kwargs):
        gl = greenlet(fn)

        async def run():
            coro = gl.switch(*args, **kwargs)
            while gl:
                try:
                    result = await coro
                except:  # noqa: E722
                    # this catches exceptions from async functions awaited in
                    # sync code, and re-raises them in the greenlet
                    coro = gl.throw(*sys.exc_info())
                else:
                    coro = gl.switch(result)
            return coro

        if with_context:
            gl.gr_context = contextvars.copy_context()
            try:
                result = await run()
            finally:
                # restore the context
                for var in gl.gr_context:
                    var.set(gl.gr_context[var])
        else:
            result = await run()

        return result

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
        parent = getcurrent().parent or bridge.start()
        if parent == getcurrent():
            raise RuntimeError(
                'await_ cannot be called from the asyncio task')
        return parent.switch(coro_or_fn)
    else:
        # assume decorator usage
        @functools.wraps(coro_or_fn)
        def decorator(*args, **kwargs):
            return await_(coro_or_fn(*args, **kwargs))

        return decorator
