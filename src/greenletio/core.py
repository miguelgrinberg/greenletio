import asyncio
import contextvars
import functools
import sys
from greenlet import greenlet, getcurrent


def _restore_context(context):
    # Check for changes in contextvars, and set them to the current
    # context for downstream consumers
    for cvar in context:
        try:
            if cvar.get() != context.get(cvar):
                cvar.set(context.get(cvar))
        except LookupError:
            cvar.set(context.get(cvar))


class GreenletBridge:
    def __init__(self):
        self.bridge_greenlet = None

    def run(self):
        async def async_run():
            gl = getcurrent().parent
            coro = gl.switch()
            while gl and coro != ():  # pragma: no branch
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
            # we shouldn't be here is a loop is already running!
            return greenlet.getcurrent()

        self.switch()
        return self.bridge_greenlet

    def stop(self):
        if self.bridge_greenlet:
            self.bridge_greenlet.switch()
            self.bridge_greenlet = None

    def switch(self):
        if self.bridge_greenlet is not None:
            raise RuntimeError('Bridge already started.')
        self.bridge_greenlet = greenlet(self.run)
        return self.bridge_greenlet.switch()


bridge = GreenletBridge()


def async_(fn=None, copy_context=False, copyback_context=False):
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
    :param copy_context: pass current contextvars.Context to greenlet (make available in fn)
    :param copyback_context: reflect changes made in greenlet in current context
        Using this option together with `copy_context` make this call similar to awaiting normal async function
    """

    if fn is None:
        return functools.partial(async_, copy_context=copy_context, copyback_context=copyback_context)

    @functools.wraps(fn)
    async def wrapper(*args, **kwargs):
        gl = greenlet(fn)
        if copy_context:
            gl.gr_context = contextvars.copy_context()
        coro = gl.switch(*args, **kwargs)
        while gl:
            try:
                result = await coro
            except:  # noqa: E722
                coro = gl.throw(*sys.exc_info())
            else:
                coro = gl.switch(result)

        if copyback_context:
            _restore_context(gl.gr_context)

        return coro

    return wrapper


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
        parent = greenlet.getcurrent().parent or bridge.start()
        if parent == greenlet.getcurrent():
            raise RuntimeError(
                'await_ cannot be called from the asyncio task')
        return parent.switch(coro_or_fn)
    else:
        # assume decorator usage
        @functools.wraps(coro_or_fn)
        def decorator(*args, **kwargs):
            return await_(coro_or_fn(*args, **kwargs))

        return decorator
