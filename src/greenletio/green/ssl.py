import os
import sys
from greenletio.io import wait_to_read, wait_to_write
from greenletio.patcher import copy_globals
from ssl import SSLWantReadError, SSLWantWriteError, PROTOCOL_TLS, Purpose, \
    CERT_NONE, CERT_REQUIRED, _ASN1Object
import ssl as _original_ssl_

copy_globals(_original_ssl_, globals())


class SSLContext(_original_ssl_.SSLContext):
    sslsocket_class = None

    def wrap_socket(self, sock, server_side=False,
                    do_handshake_on_connect=True,
                    suppress_ragged_eofs=True,
                    server_hostname=None, session=None):
        if hasattr(_original_ssl_.SSLSocket, '_create'):
            # python 3.7+
            return self.sslsocket_class._create(
                sock=sock,
                server_side=server_side,
                do_handshake_on_connect=do_handshake_on_connect,
                suppress_ragged_eofs=suppress_ragged_eofs,
                server_hostname=server_hostname,
                context=self,
                session=session
            )
        else:  # pragma: no cover
            # python 3.6
            return SSLSocket(sock=sock, server_side=server_side,
                             do_handshake_on_connect=do_handshake_on_connect,
                             suppress_ragged_eofs=suppress_ragged_eofs,
                             server_hostname=server_hostname,
                             _context=self, _session=session)


class SSLSocket(_original_ssl_.SSLSocket):
    if hasattr(_original_ssl_.SSLSocket, '_create'):
        @classmethod
        def _create(cls, *args, **kwargs):
            do_handshake_on_connect = kwargs.get(
                'do_handshake_on_connect', True)
            kwargs['do_handshake_on_connect'] = False
            sock = super(SSLSocket, cls)._create(*args, **kwargs)
            sock.do_handshake_on_connect = do_handshake_on_connect
            if sock._connected and do_handshake_on_connect:
                try:
                    sock.do_handshake()
                except (OSError, ValueError):  # pragma: no cover
                    sock.close()
                    raise
            return sock
    else:  # pragma: no cover
        def __init__(self, *args, **kwargs):
            do_handshake_on_connect = kwargs.get(
                'do_handshake_on_connect', True)
            kwargs['do_handshake_on_connect'] = False
            super().__init__(*args, **kwargs)
            self.do_handshake_on_connect = do_handshake_on_connect
            if self._connected and do_handshake_on_connect:
                self.do_handshake_on_connect = True
                try:
                    self.do_handshake()
                except (OSError, ValueError):
                    self.close()
                    raise

    def _nonblocking_io(self, method, *args, **kwargs):
        self.setblocking(False)
        while True:
            try:
                ret = method(*args, **kwargs)
                break
            except SSLWantReadError:
                wait_to_read(self.fileno())
            except SSLWantWriteError:  # pragma: no cover
                wait_to_write(self.fileno())
        return ret

    def do_handshake(self):
        return self._nonblocking_io(super().do_handshake)

    def accept(self, *args, **kwargs):
        wait_to_read(self.fileno())
        return self._nonblocking_io(super().accept, *args, **kwargs)

    def recv(self, *args, **kwargs):
        return self._nonblocking_io(super().recv, *args, **kwargs)

    def recv_into(self, *args, **kwargs):  # pragma: no cover
        return self._nonblocking_io(super().recv_into, *args, **kwargs)

    def send(self, *args, **kwargs):
        return self._nonblocking_io(super().send, *args, **kwargs)

    def sendall(self, data, flags=0):
        tail = self.send(data, flags)
        len_data = len(data)
        while tail < len_data:  # pragma: no cover
            tail += self.send(data[tail:], flags)

    def sendfile(self, *args, **kwargs):  # pragma: no cover
        raise RuntimeError('socket.sendfile is not supported')


SSLContext.sslsocket_class = SSLSocket


def create_default_context(purpose=Purpose.SERVER_AUTH, *, cafile=None,
                           capath=None, cadata=None):  # pragma: no cover
    """Create a SSLContext object with default settings.
    NOTE: The protocol and settings may change anytime without prior
          deprecation. The values represent a fair balance between maximum
          compatibility and security.
    """
    if not isinstance(purpose, _ASN1Object):
        raise TypeError(purpose)

    # SSLContext sets OP_NO_SSLv2, OP_NO_SSLv3, OP_NO_COMPRESSION,
    # OP_CIPHER_SERVER_PREFERENCE, OP_SINGLE_DH_USE and OP_SINGLE_ECDH_USE
    # by default.
    context = SSLContext(PROTOCOL_TLS)

    if purpose == Purpose.SERVER_AUTH:
        # verify certs and host name in client mode
        context.verify_mode = CERT_REQUIRED
        context.check_hostname = True

    if cafile or capath or cadata:
        context.load_verify_locations(cafile, capath, cadata)
    elif context.verify_mode != CERT_NONE:
        # no explicit cafile, capath or cadata but the verify mode is
        # CERT_OPTIONAL or CERT_REQUIRED. Let's try to load default system
        # root CA certificates for the given purpose. This may fail silently.
        context.load_default_certs(purpose)
    # OpenSSL 1.1.1 keylog file
    if hasattr(context, 'keylog_filename'):
        keylogfile = os.environ.get('SSLKEYLOGFILE')
        if keylogfile and not sys.flags.ignore_environment:
            context.keylog_filename = keylogfile
    return context


def wrap_socket(sock, keyfile=None, certfile=None,
                server_side=False, cert_reqs=CERT_NONE,
                ssl_version=PROTOCOL_TLS, ca_certs=None,
                do_handshake_on_connect=True,
                suppress_ragged_eofs=True,
                ciphers=None):  # pragma: no cover

    if server_side and not certfile:
        raise ValueError("certfile must be specified for server-side "
                         "operations")
    if keyfile and not certfile:
        raise ValueError("certfile must be specified")
    context = SSLContext(ssl_version)
    context.verify_mode = cert_reqs
    if ca_certs:
        context.load_verify_locations(ca_certs)
    if certfile:
        context.load_cert_chain(certfile, keyfile)
    if ciphers:
        context.set_ciphers(ciphers)
    return context.wrap_socket(
        sock=sock, server_side=server_side,
        do_handshake_on_connect=do_handshake_on_connect,
        suppress_ragged_eofs=suppress_ragged_eofs
    )
