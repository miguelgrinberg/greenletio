import asyncio
import sys
import unittest
from greenletio.core import bridge, async_
from greenletio.green import socket, ssl

# Tests in this module use server and client certificates
#
# To generate server certificate:
# openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365
# -nodes -subj "/CN=example.com"
#
# To generate client certificate:
# openssl req -x509 -newkey rsa:4096 -keyout client.key -out client.crt
# -days 365 -nodes -subj "/CN=example.com"

if not hasattr(asyncio, 'create_task'):
    asyncio.create_task = asyncio.ensure_future


class TestSSL(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        bridge.stop()

    def test_sendall_recv(self):
        var = None

        @async_
        def server():
            server_socket = socket.socket()
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind(('127.0.0.1', 7000))
            server_socket.listen(5)
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            context.load_cert_chain('tests/server.crt', 'tests/server.key')
            context.load_verify_locations('tests/client.crt')
            ssl_socket = context.wrap_socket(server_socket, server_side=True)
            conn, _ = ssl_socket.accept()
            data = conn.recv(1024)
            conn.sendall(data.upper())
            conn.close()
            ssl_socket.close()

        @async_
        def client():
            nonlocal var
            client_socket = socket.socket()
            context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH,
                                                 cafile='tests/server.crt')
            context.load_cert_chain('tests/client.crt', 'tests/client.key')
            ssl_socket = context.wrap_socket(client_socket,
                                             server_hostname='example.com')
            ssl_socket.connect(('127.0.0.1', 7000))
            ssl_socket.sendall(b'hello')
            var = ssl_socket.recv(1024)
            ssl_socket.close()

        async def main():
            nonlocal var
            asyncio.create_task(server())
            asyncio.create_task(client())
            while var is None:
                await asyncio.sleep(0)

        if sys.platform == 'win32':
            loop = asyncio.SelectorEventLoop()
            asyncio.set_event_loop(loop)
        asyncio.get_event_loop().run_until_complete(main())
        assert var == b'HELLO'
