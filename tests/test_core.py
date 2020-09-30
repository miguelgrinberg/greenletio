import asyncio
import unittest
import pytest
import sys
from greenletio import async_, await_, spawn
from greenletio.core import bridge


class TestCore(unittest.TestCase):
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
        assert not asyncio.get_event_loop().is_running()

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
        assert not asyncio.get_event_loop().is_running()

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

    def test_spawn(self):
        var = 0

        def a(arg):
            nonlocal var
            var += arg

        def b(arg):
            nonlocal var
            var += arg

        async def c():
            ga = spawn(a, 40)
            gb = spawn(b, 2)
            while not ga.dead or not gb.dead:
                await asyncio.sleep(0)

        asyncio.get_event_loop().run_until_complete(c())
        assert var == 42

    @pytest.mark.skipif(sys.version_info < (3, 7), reason="contextvars module is available since 3.7")
    def test_contextvars(self):
        import contextvars
        var = contextvars.ContextVar(__name__)

        @async_
        def foo():
            assert var.get() == 1
            var.set(3)
            assert var.get() == 3

        async def bar():
            assert var.get() == 1
            var.set(2)
            assert var.get() == 2

        async def test_it():
            var.set(1)
            await asyncio.create_task(bar())
            assert var.get() == 1
            await foo()
            assert var.get() == 1
            await bar()
            assert var.get() == 2
        asyncio.get_event_loop().run_until_complete(test_it())
