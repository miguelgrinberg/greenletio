from greenletio.io import wait_to_read, wait_to_write
from greenletio.patcher import copy_globals
from ssl import SSLWantReadError, SSLWantWriteError, CERT_NONE, PROTOCOL_TLS
import ssl as __original_ssl

copy_globals(__original_ssl, globals())


class SSLContext(__original_ssl.SSLContext):
    pass


class SSLSocket(__original_ssl.SSLSocket):
    @classmethod
    def _create(cls, *args, **kwargs):
        do_handshake_on_connect = kwargs.get('do_handshake_on_connect')
        kwargs['do_handshake_on_connect'] = False
        sock = super()._create(*args, **kwargs)
        if sock._connected and do_handshake_on_connect:
            sock.do_handshake_on_connect = True
            try:
                sock._do_nonblocking_handshake()
            except (OSError, ValueError):
                sock.close()
                raise
        return sock

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

    def sendall(self, *args, **kwargs):
        return self._nonblocking_io(super().sendall, *args, **kwargs)

    def sendto(self, *args, **kwargs):
        return self._nonblocking_io(super().sendto, *args, **kwargs)

    def sendmsg(self, *args, **kwargs):
        return self._nonblocking_io(super().sendmsg, *args, **kwargs)

    def sendmsg_afalg(self, *args, **kwargs):
        return self._nonblocking_io(super().sendmsg_afalg, *args, **kwargs)

    def sendfile(self, *args, **kwargs):
        return self._nonblocking_io(super().sendfile, *args, **kwargs)


SSLContext.sslsocket_class = SSLSocket


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
