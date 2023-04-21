import asyncio
import collections
import weakref
import greenlet
from greenletio.core import await_, async_
from greenletio.patcher import copy_globals
import threading as _original_threading_

copy_globals(_original_threading_, globals())

_active = {}


def get_ident():
    return id(greenlet.getcurrent())


class Lock:
    def __init__(self):
        self._lock = asyncio.Lock()
        self.locked = self._lock.locked
        self.release = self._lock.release

    def acquire(self, blocking=True, timeout=None):
        if not blocking and self.locked():
            return False
        if timeout is None or timeout < 0:
            return await_(self._lock.acquire())
        else:
            try:
                return await_(asyncio.wait_for(self._lock.acquire(), timeout))
            except asyncio.TimeoutError:
                return False

    def __enter__(self):
        return self.acquire()

    def __exit__(self, *args):
        return self.release()


class RLock:
    def __init__(self):
        self._lock = Lock()
        self.owner = None
        self.count = 0
        self.locked = self._lock.locked

    def __repr__(self):  # pragma: no cover
        owner = self.owner
        try:
            owner = _active[owner].name
        except KeyError:
            pass
        r = super().__repr__().split(' ', 1)
        return "<%s.%s %s, owner=%s, count=%d]>" % (
            self.__class__.__module__,
            self.__class__.__qualname__,
            r[1][:-2],
            owner,
            self.count)

    def acquire(self, blocking=True, timeout=-1):
        me = get_ident()
        if self.owner == me:
            self.count += 1
            return True
        ret = self._lock.acquire(blocking, timeout)
        if ret:
            self.owner = me
            self.count = 1
        return ret

    def release(self):
        if self.owner != get_ident():
            raise RuntimeError("cannot release un-acquired lock")
        self.count = self.count - 1
        if not self.count:
            self.owner = None
            self._lock.release()

    def __enter__(self):
        return self.acquire()

    def __exit__(self, *args):
        return self.release()


class Condition:
    def __init__(self, lock=None):
        if lock is None:
            lock = RLock()
        self._lock = lock
        self.locked = lock.locked
        self.acquire = lock.acquire
        self.release = lock.release
        self._waiters = collections.deque()

    def __repr__(self):  # pragma: no cover
        res = super().__repr__()
        extra = 'locked' if self.locked() else 'unlocked'
        if self._waiters:
            extra = f'{extra}, waiters:{len(self._waiters)}'
        return f'<{res[1:-1]} [{extra}]>'

    def wait(self, timeout=None):
        if not self.locked():
            raise RuntimeError('cannot wait on un-acquired lock')

        self.release()
        try:
            fut = asyncio.get_event_loop().create_future()
            self._waiters.append(fut)
            try:
                if timeout is None:
                    await_(fut)
                else:
                    try:
                        await_(asyncio.wait_for(fut, timeout))
                    except asyncio.TimeoutError:
                        return False
                return True
            finally:
                self._waiters.remove(fut)
        finally:
            cancelled = False
            while True:
                try:
                    self.acquire()
                    break
                except asyncio.CancelledError:  # pragma: no cover
                    cancelled = True
            if cancelled:  # pragma: no cover
                raise asyncio.CancelledError

    def wait_for(self, predicate, timeout=None):
        result = predicate()
        while not result:
            self.wait(timeout)
            result = predicate()
        return result

    def notify(self, n=1):
        if not self.locked():
            raise RuntimeError('cannot notify on un-acquired lock')

        idx = 0
        for fut in self._waiters:
            if idx >= n:  # pragma: no cover
                break

            if not fut.done():  # pragma: no cover
                idx += 1
                fut.set_result(False)

    def notify_all(self):
        self.notify(len(self._waiters))

    notifyAll = notify_all

    def __enter__(self):
        return self.acquire()

    def __exit__(self, *args):
        return self.release()


class Semaphore:
    def __init__(self, value=1):
        self._sem = asyncio.Semaphore(value)
        self.release = self._sem.release

    def acquire(self, blocking=True, timeout=None):
        if timeout is None:
            return await_(self._sem.acquire())
        else:
            try:
                return await_(asyncio.wait_for(self._sem.acquire(), timeout))
            except asyncio.TimeoutError:
                return False

    def __enter__(self):
        return self.acquire()

    def __exit__(self, *args):
        return self.release()


class BoundedSemaphore(Semaphore):
    def __init__(self, value=1):
        self._sem = asyncio.BoundedSemaphore(value)
        self.release = self._sem.release


class Event(asyncio.Event):
    def wait(self, timeout=None):
        if timeout is None:
            return await_(super().wait())
        else:
            try:
                return await_(asyncio.wait_for(super().wait(), timeout))
            except asyncio.TimeoutError:
                return False

    isSet = asyncio.Event.is_set


class Barrier(_original_threading_.Barrier):
    def __init__(self, parties, action=None, timeout=None):
        self._cond = Condition(Lock())
        self._action = action
        self._timeout = timeout
        self._parties = parties
        self._state = 0
        self._count = 0


class Thread(_original_threading_.Thread):
    def __init__(self, group=None, target=None, name=None, args=(),
                 kwargs=None, *, daemon=None):
        assert group is None, "group argument must be None for now"
        if kwargs is None:
            kwargs = {}
        self._target = target
        self._name = str(name or _original_threading_._newname('GThread-%d'))
        self._args = args
        self._kwargs = kwargs
        self._daemonic = False
        self._ident = None
        self._started = Event()
        self._ended = Event()
        self._is_stopped = False
        self._initialized = True
        self._task = None

    def start(self):
        if not self._initialized:  # pragma: no cover
            raise RuntimeError("thread.__init__() not called")

        if self._started.is_set():
            raise RuntimeError("threads can only be started once")

        async def bootstrap():
            await async_(self._bootstrap)()

        self.task = asyncio.ensure_future(bootstrap())
        self._started.set()

    def _set_ident(self):
        self._ident = get_ident()

    def _bootstrap(self):
        self._set_ident()
        _active[self._ident] = self
        try:
            self.run()
        finally:
            self._is_stopped = True
            del _active[self._ident]
            self._ended.set()

    def join(self, timeout=None):
        if not self._initialized:  # pragma: no cover
            raise RuntimeError("Thread.__init__() not called")
        if not self._started.is_set():
            raise RuntimeError("cannot join thread before it is started")
        if self is current_thread():
            raise RuntimeError("cannot join current thread")

        self._ended.wait()

    def is_alive(self):
        assert self._initialized, "Thread.__init__() not called"
        return not self._is_stopped and self._started.is_set()


class _DummyThread(Thread):

    def __init__(self):
        Thread.__init__(self, name=_original_threading_._newname("Dummy-%d"),
                        daemon=True)
        self._set_ident()
        _active[self._ident] = self

    def _stop(self):  # pragma: no cover
        pass

    def is_alive(self):  # pragma: no cover
        assert not self._is_stopped and self._started.is_set()
        return True

    def join(self, timeout=None):  # pragma: no cover
        assert False, "cannot join a dummy thread"


def current_thread():
    try:
        return _active[get_ident()]
    except KeyError:
        return _DummyThread()


class Timer(Thread):
    def __init__(self, interval, function, args=None, kwargs=None):
        Thread.__init__(self)
        self.interval = interval
        self.function = function
        self.args = args if args is not None else []
        self.kwargs = kwargs if kwargs is not None else {}
        self.finished = Event()

    def cancel(self):
        """Stop the timer if it hasn't finished yet."""
        self.finished.set()

    def run(self):
        self.finished.wait(self.interval)
        if not self.finished.is_set():
            self.function(*self.args, **self.kwargs)
        self.finished.set()


class _localbase(object):
    __slots__ = '_local__args', '_local__greens'

    def __new__(cls, *args, **kw):
        self = object.__new__(cls)
        object.__setattr__(self, '_local__args', (args, kw))
        object.__setattr__(self, '_local__greens', weakref.WeakKeyDictionary())
        if (args or kw) and \
                (cls.__init__ is object.__init__):  # pragma: no cover
            raise TypeError("Initialization arguments are not supported")
        return self


def _patch(thrl):
    greens = object.__getattribute__(thrl, '_local__greens')
    cur = greenlet.getcurrent()
    if cur not in greens:
        greens[cur] = {}
        cls = type(thrl)
        if cls.__init__ is not object.__init__:
            args, kw = object.__getattribute__(thrl, '_local__args')
            thrl.__init__(*args, **kw)
    object.__setattr__(thrl, '__dict__', greens[cur])


class local(_localbase):
    def __getattribute__(self, attr):
        _patch(self)
        return object.__getattribute__(self, attr)

    def __setattr__(self, attr, value):
        _patch(self)
        return object.__setattr__(self, attr, value)

    def __delattr__(self, attr):
        _patch(self)
        return object.__delattr__(self, attr)
