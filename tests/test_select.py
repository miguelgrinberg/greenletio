import asyncio
import sys
import unittest
from greenletio.core import bridge, async_
from greenletio.green import socket, selectors, time
from .util import run_coro


class TestSelect(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        bridge.stop()

    def test_send_recv(self):
        var = None

        @async_
        def server():
            sel = selectors.DefaultSelector()
            server_socket = socket.socket()
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind(('127.0.0.1', 7000))
            server_socket.listen(5)

            sel.register(server_socket, selectors.EVENT_READ)
            events = sel.select()
            assert len(events) == 1
            assert events[0][0].fileobj == server_socket
            assert events[0][0].events == selectors.EVENT_READ
            conn, _ = server_socket.accept()
            sel.unregister(server_socket)

            sel.register(conn, selectors.EVENT_READ)
            events = sel.select()
            assert len(events) == 1
            assert events[0][0].fileobj == conn
            assert events[0][0].events == selectors.EVENT_READ
            data = conn.recv(1024)
            sel.unregister(conn)

            sel.register(conn, selectors.EVENT_WRITE)
            events = sel.select()
            assert len(events) == 1
            assert events[0][0].fileobj == conn
            assert events[0][0].events == selectors.EVENT_WRITE
            conn.sendall(data.upper())
            sel.unregister(conn)
            conn.close()
            server_socket.close()

        @async_
        def client():
            nonlocal var
            client_socket = socket.socket()
            client_socket.connect(('127.0.0.1', 7000))
            time.sleep(0.1)
            client_socket.sendall(b'hello')
            time.sleep(0.1)
            var = client_socket.recv(1024)
            client_socket.close()

        async def main():
            nonlocal var
            asyncio.create_task(server())
            asyncio.create_task(client())
            while var is None:
                await asyncio.sleep(0)

        run_coro(main())
        assert var == b'HELLO'
