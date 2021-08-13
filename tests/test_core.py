import asyncio
import unittest
import pytest
from greenletio import async_, await_
from greenletio.core import bridge


class TestCore(unittest.TestCase):
    def setUp(self):
        pass

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

        @async_
        def c(arg):
            return arg

        async def d(arg):
            assert await(c(arg)) == arg
            return await b(arg)

        ret = asyncio.get_event_loop().run_until_complete(d(42))
        assert ret == 42
        assert var == 42

    def test_async_await_exception(self):
        @async_
        def a(arg):
            raise RuntimeError(arg)

        async def b(arg):
            with pytest.raises(RuntimeError) as error:
                await a(arg)
            assert type(error.value) == RuntimeError and \
                str(error.value) == '42'

        asyncio.get_event_loop().run_until_complete(b(42))

    def test_async_await_exception2(self):
        async def a(arg):
            raise RuntimeError(arg)

        @async_
        def b(arg):
            with pytest.raises(RuntimeError) as error:
                await_(a(arg))
            assert type(error.value) == RuntimeError and \
                str(error.value) == '42'

        async def c(arg):
            await b(arg)

        asyncio.get_event_loop().run_until_complete(c(42))

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
        assert ret == [1, 3] or ret == [3, 2]

    def test_await_raises_exception(self):
        async def a(arg):
            raise RuntimeError('foo')

        with pytest.raises(RuntimeError) as exc:
            await_(a(42))
        assert str(exc.value) == 'foo'

    def test_async_raises_exception(self):
        @async_
        def a(arg):
            raise RuntimeError('foo')

        async def b():
            with pytest.raises(RuntimeError) as exc:
                await a(42)
            assert str(exc.value) == 'foo'

        asyncio.get_event_loop().run_until_complete(b())

    def test_await_after_exception(self):
        async def a():
            raise RuntimeError('foo')

        async def b():
            return 42

        @async_
        def c():
            try:
                await_(a())
            except RuntimeError as exc:
                assert str(exc) == 'foo'
            assert await_(b()) == 42

        asyncio.get_event_loop().run_until_complete(c())

    def test_bad_await_with_external_loop(self):
        @async_
        def a():
            await_(asyncio.sleep(0))

        def b():
            with pytest.raises(RuntimeError):
                await_(asyncio.sleep(0))
            assert bridge.bridge_greenlet is None

        async def c():
            await a()
            b()

        asyncio.get_event_loop().run_until_complete(c())
        assert bridge.bridge_greenlet is None

    def bad_await_with_internal_loop(self):
        async def a():
            with pytest.raises(RuntimeError):
                await_(asyncio.sleep(0))

        await_(a())

    def test_switch_bridge_twice(self):
        bridge.start()
        with pytest.raises(RuntimeError):
            bridge.switch()
