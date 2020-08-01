from greenletio.io import wait_to_read, wait_to_write
from greenletio.patcher import copy_globals
from ssl import SSLWantReadError, SSLWantWriteError, CERT_NONE, PROTOCOL_TLS
import ssl as _original_ssl_

copy_globals(_original_ssl_, globals())


class SSLContext(_original_ssl_.SSLContext):
    sslsocket_class = None

    def wrap_socket(self, sock, server_side=False,
                    do_handshake_on_connect=True,
                    suppress_ragged_eofs=True,
                    server_hostname=None, session=None):
        if hasattr(_original_ssl_.SSLSocket, '_create'):
            return self.sslsocket_class._create(
                sock=sock,
                server_side=server_side,
                do_handshake_on_connect=do_handshake_on_connect,
                suppress_ragged_eofs=suppress_ragged_eofs,
                server_hostname=server_hostname,
                context=self,
                session=session
            )
        else:
            return SSLSocket(sock=sock, server_side=server_side,
                             do_handshake_on_connect=do_handshake_on_connect,
                             suppress_ragged_eofs=suppress_ragged_eofs,
                             server_hostname=server_hostname,
                             _context=self, _session=session)


class SSLSocket(_original_ssl_.SSLSocket):
    if hasattr(_original_ssl_.SSLSocket, '_create'):
        @classmethod
        def _create(cls, *args, **kwargs):
            do_handshake_on_connect = kwargs.get('do_handshake_on_connect')
            kwargs['do_handshake_on_connect'] = False
            sock = super(SSLSocket, cls)._create(*args, **kwargs)
            if sock._connected and do_handshake_on_connect:
                sock.do_handshake_on_connect = True
                try:
                    sock._do_nonblocking_handshake()
                except (OSError, ValueError):
                    sock.close()
                    raise
            return sock
    else:
        def __init__(self, *args, **kwargs):
            do_handshake_on_connect = kwargs.get('do_handshake_on_connect')
            kwargs['do_handshake_on_connect'] = False
            super().__init__(*args, **kwargs)
            if self._connected and do_handshake_on_connect:
                self.do_handshake_on_connect = True
                try:
                    self._do_nonblocking_handshake()
                except (OSError, ValueError):
                    self.close()
                    raise

    def _do_nonblocking_handshake(self):
        while True:
            try:
                self.do_handshake()
                break
            except SSLWantReadError:
                wait_to_read(self.fileno())
            except SSLWantWriteError:
                wait_to_write(self.fileno())

    def _nonblocking_io(self, method, *args, **kwargs):
        self.setblocking(False)
        while True:
            try:
                ret = method(*args, **kwargs)
            except SSLWantReadError:
                wait_to_read(self.fileno())
            except SSLWantWriteError:
                wait_to_write(self.fileno())
            else:
                break
        return ret

    def accept(self, *args, **kwargs):
        wait_to_read(self.fileno())
        conn, address = self._nonblocking_io(super().accept, *args, **kwargs)
        conn.setblocking(False)
        conn = self.context.wrap_socket(
            conn, do_handshake_on_connect=self.do_handshake_on_connect,
            suppress_ragged_eofs=self.suppress_ragged_eofs, server_side=True)
        return conn, address

    def recv(self, *args, **kwargs):
        return self._nonblocking_io(super().recv, *args, **kwargs)

    def recvfrom(self, *args, **kwargs):
        return self._nonblocking_io(super().recvfrom, *args, **kwargs)

    def recvmsg(self, *args, **kwargs):
        return self._nonblocking_io(super().recvmsg, *args, **kwargs)

    def recvmsg_into(self, *args, **kwargs):
        return self._nonblocking_io(super().recvmsg_into, *args, **kwargs)

    def recvfrom_into(self, *args, **kwargs):
        return self._nonblocking_io(super().recvfrom_into, *args, **kwargs)

    def recv_into(self, *args, **kwargs):
        return self._nonblocking_io(super().recv_into, *args, **kwargs)

    def send(self, *args, **kwargs):
        return self._nonblocking_io(super().send, *args, **kwargs)

    def sendall(self, data, flags=0):
        tail = self.send(data, flags)
        len_data = len(data)
        while tail < len_data:  # pragma: no cover
            tail += self.send(data[tail:], flags)

    def sendto(self, *args, **kwargs):
        return self._nonblocking_io(super().sendto, *args, **kwargs)

    def sendmsg(self, *args, **kwargs):
        return self._nonblocking_io(super().sendmsg, *args, **kwargs)

    def sendmsg_afalg(self, *args, **kwargs):
        return self._nonblocking_io(super().sendmsg_afalg, *args, **kwargs)

    def sendfile(self, *args, **kwargs):
        raise RuntimeError('socket.sendfile is not supported')


SSLContext.sslsocket_class = SSLSocket


def create_default_context(purpose=Purpose.SERVER_AUTH, *, cafile=None,
                           capath=None, cadata=None):
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
                ciphers=None):

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
