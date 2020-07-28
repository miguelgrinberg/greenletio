import asyncio
import unittest
from greenletio import spawn
from greenletio.core import bridge
from greenletio.green import socket


class TestSocket(unittest.TestCase):
    def setUp(self):
        bridge.reset()

    def tearDown(self):
        bridge.stop()

    def test_send_recv(self):
        var = None

        def server():
            server_socket = socket.socket()
            print('a')
            server_socket.bind(('127.0.0.1', 7000))
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.listen(5)
            conn, _ = server_socket.accept()
            data = conn.recv(1024)
            conn.send(data.upper())
            conn.close()
            server_socket.close()

        def client():
            global var
            client_socket = socket.socket()
            client_socket.connect(('127.0.0.1', 7000))
            client_socket.send(b'hello')
            var = client_socket.recv(1024)
            client_socket.close()

        async def main():
            spawn(server)
            spawn(client)
            while var is None:
                await asyncio.sleep(0.01)

        asyncio.get_event_loop().run_until_complete(main())
        assert var == b'HELLO'
