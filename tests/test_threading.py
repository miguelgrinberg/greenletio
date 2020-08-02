import unittest
import pytest
from greenletio.core import bridge
from greenletio.green import threading, time


class TestThreading(unittest.TestCase):
    def setUp(self):
        bridge.reset()

    def tearDown(self):
        bridge.stop()

    def test_lock(self):
        var = None
        lock = threading.Lock()

        def t1():
            nonlocal var
            with pytest.raises(RuntimeError):
                lock.release()
            with lock:
                time.sleep(0.05)
                var = 'foo'

        def t2():
            nonlocal var
            time.sleep(0.02)
            assert lock.acquire(blocking=False) is False
            assert lock.acquire(timeout=0.01) is False
            with lock:
                assert var == 'foo'
                var = 'bar'

        th1 = threading.Thread(target=t1)
        th2 = threading.Thread(target=t2)
        th1.start()
        th2.start()
        th1.join()
        th2.join()
        assert var == 'bar'

    def test_rlock(self):
        var = None
        lock = threading.RLock()

        def t1():
            nonlocal var
            with lock:
                with lock:
                    var = 'foo'
                    time.sleep(0.05)

        def t2():
            nonlocal var
            time.sleep(0.02)
            assert lock.acquire(blocking=False) is False
            with pytest.raises(RuntimeError):
                lock.release()
            with lock:
                with lock:
                    assert var == 'foo'
                    var = 'bar'

        th1 = threading.Thread(target=t1)
        th2 = threading.Thread(target=t2)
        th1.start()
        th2.start()
        th1.join()
        th2.join()
        assert var == 'bar'

    def test_condition(self):
        var = None
        cv = threading.Condition()

        def consumer():
            nonlocal var
            with pytest.raises(RuntimeError):
                cv.wait()
            with cv:
                assert cv.wait(timeout=0) is False
                cv.wait()
                assert var == 'foo'
                var = 'bar'

        def producer():
            nonlocal var
            with pytest.raises(RuntimeError):
                cv.notify()
            time.sleep(0.05)
            with cv:
                var = 'foo'
                cv.notify_all()

        th1 = threading.Thread(target=consumer)
        th2 = threading.Thread(target=producer)
        th1.start()
        th2.start()
        th1.join()
        th2.join()
        assert var == 'bar'

    def test_semaphore(self):
        var = None
        sem = threading.Semaphore()

        def t():
            nonlocal var
            for i in range(10):
                with sem:
                    assert var is None
                    var = 'foo'
                    time.sleep(0)
                    var = None

        ths = [threading.Thread(target=t) for i in range(5)]
        for th in ths:
            th.start()
        for th in ths:
            th.join()
        assert var is None

    def test_bounded_semaphore(self):
        var = 0
        sem = threading.BoundedSemaphore(2)

        def t():
            nonlocal var
            for i in range(10):
                with sem:
                    assert var <= 1
                    var += 1
                    time.sleep(0)
                    var -= 1

        ths = [threading.Thread(target=t) for i in range(5)]
        for th in ths:
            th.start()
        for th in ths:
            th.join()
        assert var == 0
        with pytest.raises(ValueError):
            sem.release()

    def test_event(self):
        var = None
        ev = threading.Event()

        def t():
            nonlocal var
            time.sleep(0.05)
            var = 'foo'
            ev.set()

        th = threading.Thread(target=t)
        th.start()
        assert not ev.is_set()
        ev.wait()
        assert ev.is_set()
        assert var == 'foo'

    def test_timer(self):
        var = None

        def t(arg):
            nonlocal var
            var = arg

        tm = threading.Timer(0.05, t, (42,))
        tm.start()
        assert var is None
        tm.join()
        assert var == 42

    def test_timer_canceled(self):
        var = None

        def t(arg):
            nonlocal var
            var = arg

        tm = threading.Timer(0.05, t, (42,))
        tm.start()
        tm.cancel()
        assert var is None
        tm.join()
        assert var is None

    def test_barrier(self):
        var = [0, 0, 0, 0, 0, 0]
        b = threading.Barrier(6)

        def t():
            time.sleep(0.05)
            ret = b.wait()
            var[ret] = 1

        ths = [threading.Thread(target=t) for i in range(5)]
        for th in ths:
            th.start()
        ret = b.wait()
        for th in ths:
            th.join()
        for i in range(len(var)):
            assert var[i] == 0 if i == ret else 1

    def test_local(self):
        local = threading.local()

        def t(n):
            local.var = n
            time.sleep(0.05)
            assert local.var == n

        local.var = 'foo'
        ths = [threading.Thread(target=t, args=(i,)) for i in range(5)]
        for th in ths:
            th.start()
        for th in ths:
            th.join()
        assert local.var == 'foo'
        del local.var
        with pytest.raises(AttributeError):
            local.var

    def test_local_object(self):
        class MyLocal(threading.local):
            def __init__(self, n):
                self.var = n

        local = MyLocal('foo')

        def t(n):
            assert local.var == 'foo'
            local.var = n
            time.sleep(0.05)
            assert local.var == n

        local.var = 'bar'
        ths = [threading.Thread(target=t, args=(i,)) for i in range(5)]
        for th in ths:
            th.start()
        for th in ths:
            th.join()
        assert local.var == 'bar'
        del local.var
        with pytest.raises(AttributeError):
            local.var

    def test_thread(self):
        def t(foo, bar=None):
            with pytest.raises(RuntimeError):
                threading.current_thread().join()
            assert foo == 'foo'
            assert bar == 'bar'

        th = threading.Thread(target=t, args=('foo',), kwargs={'bar': 'bar'})
        with pytest.raises(RuntimeError):
            th.join()
        th.start()
        assert th.is_alive()
        th.join()
        assert th.is_alive() is False
        with pytest.raises(RuntimeError):
            th.start()
