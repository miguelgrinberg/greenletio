import platform
import socket
import sys
import threading
import unittest
from greenletio import patch_blocking, patch_psycopg2
from greenletio.green import socket as green_socket, \
    threading as green_threading


class TestPatcher(unittest.TestCase):
    def test_patch(self):
        assert 'socketserver' not in sys.modules
        if 'threading' in sys.modules:
            del sys.modules['threading']
        with patch_blocking():
            assert sys.modules['socket'] == green_socket
            assert sys.modules['threading'] == green_threading
            import socketserver
            assert socketserver.socket == green_socket
            assert '__greenletio_patched__' in sys.modules
        assert sys.modules['socket'] == socket
        assert 'threading' not in sys.modules
        assert 'socketserver' not in sys.modules
        assert '__greenletio_patched__' not in sys.modules

    def test_patch_partial(self):
        assert 'socketserver' not in sys.modules
        original_threading = sys.modules.get('threading')
        with patch_blocking(['socket']):
            assert sys.modules['socket'] == green_socket
            assert sys.modules.get('threading') == original_threading
            import socketserver
            assert socketserver.socket == green_socket
            assert '__greenletio_patched__' in sys.modules
        assert sys.modules['socket'] == socket
        assert sys.modules.get('threading') == original_threading
        assert 'socketserver' not in sys.modules
        assert '__greenletio_patched__' not in sys.modules

    def test_patch_recursive(self):
        assert 'socketserver' not in sys.modules
        if 'threading' in sys.modules:
            del sys.modules['threading']
        with patch_blocking():
            with patch_blocking():
                assert sys.modules['socket'] == green_socket
                assert sys.modules['threading'] == green_threading
                import socketserver
                assert socketserver.socket == green_socket
                assert '__greenletio_patched__' in sys.modules
            assert sys.modules['socket'] == green_socket
            assert sys.modules['threading'] == green_threading
            assert 'socketserver' not in sys.modules
            assert '__greenletio_patched__' in sys.modules
        assert sys.modules['socket'] == socket
        assert 'threading' not in sys.modules
        assert 'socketserver' not in sys.modules
        assert '__greenletio_patched__' not in sys.modules

    @unittest.skipIf(platform.python_implementation() != 'CPython',
                    'psycopg2-binary does not install on pypy3')
    def test_patch_psycopg2(self):
        import psycopg2
        assert psycopg2.extensions.get_wait_callback() is None
        patch_psycopg2()
        assert psycopg2.extensions.get_wait_callback() is not None
