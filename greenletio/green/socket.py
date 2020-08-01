import errno
from greenletio.io import wait_to_read, wait_to_write
from greenletio.patcher import copy_globals
import socket as _original_socket_

copy_globals(_original_socket_, globals())


class socket(_original_socket_.socket):
    def _nonblocking_read(self, method, *args, **kwargs):
        self.setblocking(False)
        while True:
            try:
                ret = method(*args, **kwargs)
                break
            except (OSError, BlockingIOError) as exc:
                err = exc.errno
                if err in (errno.EAGAIN, errno.EWOULDBLOCK):
                    wait_to_read(self.fileno())
                else:  # pragma: no cover
                    raise
        return ret

    def _nonblocking_write(self, method, *args, **kwargs):
        self.setblocking(False)
        while True:
            try:
                ret = method(*args, **kwargs)
                break
            except (OSError, BlockingIOError) as exc:
                err = exc.errno
                ret = None
                if err in (errno.EAGAIN, errno.EWOULDBLOCK, errno.EINPROGRESS):
                    wait_to_write(self.fileno())
                    if err == errno.EINPROGRESS:  # pragma: no cover
                        break
                else:  # pragma: no cover
                    raise
        return ret

    def accept(self, *args, **kwargs):
        wait_to_read(self.fileno())
        conn, address = self._nonblocking_read(super().accept, *args, **kwargs)
        conn.setblocking(False)
        fd = conn.detach()
        return socket(fileno=fd), address

    def connect(self, *args, **kwargs):
        return self._nonblocking_write(super().connect, *args, **kwargs)

    def connect_ex(self, *args, **kwargs):  # pragma: no cover
        return self._nonblocking_write(super().connect_ex, *args, **kwargs)

    def recv(self, *args, **kwargs):
        return self._nonblocking_read(super().recv, *args, **kwargs)

    def recvfrom(self, *args, **kwargs):
        return self._nonblocking_read(super().recvfrom, *args, **kwargs)

    def recvmsg(self, *args, **kwargs):  # pragma: no cover
        return self._nonblocking_read(super().recvmsg, *args, **kwargs)

    def recvmsg_into(self, *args, **kwargs):  # pragma: no cover
        return self._nonblocking_read(super().recvmsg_into, *args, **kwargs)

    def recvfrom_into(self, *args, **kwargs):  # pragma: no cover
        return self._nonblocking_read(super().recvfrom_into, *args, **kwargs)

    def recv_into(self, *args, **kwargs):  # pragma: no cover
        return self._nonblocking_read(super().recv_into, *args, **kwargs)

    def send(self, *args, **kwargs):
        return self._nonblocking_write(super().send, *args, **kwargs)

    def sendall(self, data, flags=0):
        tail = self.send(data, flags)
        len_data = len(data)
        while tail < len_data:  # pragma: no cover
            tail += self.send(data[tail:], flags)

    def sendto(self, *args, **kwargs):
        return self._nonblocking_write(super().sendto, *args, **kwargs)

    def sendmsg(self, *args, **kwargs):  # pragma: no cover
        return self._nonblocking_write(super().sendmsg, *args, **kwargs)

    def sendmsg_afalg(self, *args, **kwargs):  # pragma: no cover
        return self._nonblocking_write(super().sendmsg_afalg, *args, **kwargs)

    def sendfile(self, *args, **kwargs):  # pragma: no cover
        raise RuntimeError('socket.sendfile is not supported')


def create_connection(address, timeout=_GLOBAL_DEFAULT_TIMEOUT,
                      source_address=None):  # pragma: no cover
    host, port = address
    err = None
    for res in getaddrinfo(host, port, 0, SOCK_STREAM):
        af, socktype, proto, canonname, sa = res
        sock = None
        try:
            sock = socket(af, socktype, proto)
            if timeout is not _GLOBAL_DEFAULT_TIMEOUT:
                sock.settimeout(timeout)
            if source_address:
                sock.bind(source_address)
            sock.connect(sa)
            # Break explicitly a reference cycle
            err = None
            return sock

        except error as _:
            err = _
            if sock is not None:
                sock.close()

    if err is not None:
        try:
            raise err
        finally:
            # Break explicitly a reference cycle
            err = None
    else:
        raise error("getaddrinfo returns an empty list")


def create_server(address, *, family=AF_INET, backlog=None, reuse_port=False,
                  dualstack_ipv6=False):  # pragma: no cover
    if reuse_port and not hasattr(_socket, "SO_REUSEPORT"):
        raise ValueError("SO_REUSEPORT not supported on this platform")
    if dualstack_ipv6:
        if not has_dualstack_ipv6():
            raise ValueError("dualstack_ipv6 not supported on this platform")
        if family != AF_INET6:
            raise ValueError("dualstack_ipv6 requires AF_INET6 family")
    sock = socket(family, SOCK_STREAM)
    try:
        if os.name not in ('nt', 'cygwin') and \
                hasattr(_socket, 'SO_REUSEADDR'):
            try:
                sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            except error:
                pass
        if reuse_port:
            sock.setsockopt(SOL_SOCKET, SO_REUSEPORT, 1)
        if has_ipv6 and family == AF_INET6:
            if dualstack_ipv6:
                sock.setsockopt(IPPROTO_IPV6, IPV6_V6ONLY, 0)
            elif hasattr(_socket, "IPV6_V6ONLY") and \
                    hasattr(_socket, "IPPROTO_IPV6"):
                sock.setsockopt(IPPROTO_IPV6, IPV6_V6ONLY, 1)
        try:
            sock.bind(address)
        except error as err:
            msg = '%s (while attempting to bind on address %r)' % \
                (err.strerror, address)
            raise error(err.errno, msg) from None
        if backlog is None:
            sock.listen()
        else:
            sock.listen(backlog)
        return sock
    except error:
        sock.close()
        raise
