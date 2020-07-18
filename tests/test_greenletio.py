import asyncio
import unittest
import pytest
from greenletio import async_, await_
from greenletio.core import bridge


class TestGreenletio(unittest.TestCase):
    def setUp(self):
        bridge.reset()

    def tearDown(self):
        bridge.stop()

    def test_await_function_with_internal_loop(self):
        var = None

        async def a(arg):
            nonlocal var
            var = arg
            return arg

        ret = await_(a(42))
        assert ret == 42
        assert var == 42

        bridge.stop()
        assert not bridge.running
        with pytest.raises(RuntimeError):
            asyncio.get_running_loop()

    def test_await_decorator_with_internal_loop(self):
        var = None

        @await_
        async def a(arg):
            nonlocal var
            var = arg
            return arg

        ret = a(42)
        assert ret == 42
        assert var == 42

        bridge.stop()
        assert not bridge.running
        with pytest.raises(RuntimeError):
            asyncio.get_running_loop()

    def test_async_await_with_external_loop(self):
        var = None

        async def a(arg):
            nonlocal var
            var = arg
            return arg

        @async_
        def b(arg):
            return await_(a(arg))

        async def c(arg):
            return await b(arg)

        ret = asyncio.get_event_loop().run_until_complete(c(42))
        assert ret == 42
        assert var == 42

    def test_gather_with_external_loop(self):
        var = 0

        @async_
        def a():
            nonlocal var
            await_(asyncio.sleep(0.01))
            var += 1
            return var

        @async_
        def b():
            nonlocal var
            await_(asyncio.sleep(0.01))
            var += 2
            return var

        async def c():
            tasks = [a(), b()]
            return await asyncio.gather(*tasks)

        ret = asyncio.get_event_loop().run_until_complete(c())
        assert ret == [1, 3]

    def test_await_raises_exception(self):
        async def a(arg):
            raise RuntimeError('foo')

        with pytest.raises(RuntimeError) as exc:
            await_(a(42))
        assert exc.type == RuntimeError
        assert str(exc.value) == 'foo'

    def test_async_raises_exception(self):
        @async_
        def a(arg):
            raise RuntimeError('foo')

        async def b():
            with pytest.raises(RuntimeError) as exc:
                await a(42)
            assert exc.type == RuntimeError
            assert str(exc.value) == 'foo'

        asyncio.get_event_loop().run_until_complete(b())
