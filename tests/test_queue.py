import unittest
import pytest
from greenletio.core import bridge
from greenletio.green import queue, threading


class TestQueue(unittest.TestCase):
    def setUp(self):
        bridge.reset()

    def tearDown(self):
        bridge.stop()

    def test_queue(self):
        q = queue.Queue()
        var = 0

        def t():
            while True:
                nonlocal var
                try:
                    item = q.get(block=False)
                except queue.Empty:
                    break
                var += item
                q.task_done()

        q.put(42, block=False)
        assert q.qsize() == 1
        assert q.get_nowait() == 42
        q.task_done()
        q.put(42, timeout=0.01)
        assert q.get(timeout=0.01) == 42
        q.task_done()
        q.put_nowait(42)
        assert q.get_nowait() == 42
        q.task_done()
        with pytest.raises(queue.Empty):
            q.get(timeout=0.01)
        for i in range(5):
            q.put(i)
        assert q.get() == 0
        q.task_done()
        th = threading.Thread(target=t)
        th.start()
        q.join()
        th.join()
        assert q.empty()
        assert var == 10

    def test_simple_queue(self):
        q = queue.SimpleQueue()
        var = 0

        def t():
            while True:
                nonlocal var
                try:
                    item = q.get(block=False)
                except queue.Empty:
                    break
                var += item

        q.put(42, block=False)
        assert q.qsize() == 1
        assert q.get_nowait() == 42
        q.put(42, timeout=0.01)
        assert q.get(timeout=0.01) == 42
        q.put_nowait(42)
        assert q.get_nowait() == 42
        with pytest.raises(queue.Empty):
            q.get(timeout=0.01)
        for i in range(5):
            q.put(i)
        assert q.get() == 0
        th = threading.Thread(target=t)
        th.start()
        th.join()
        assert q.empty()
        assert var == 10
