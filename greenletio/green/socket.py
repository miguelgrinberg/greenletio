import errno
import os
from greenletio.io import wait_to_read, wait_to_write
from greenletio.patcher import copy_globals
from socket import _GLOBAL_DEFAULT_TIMEOUT, SOCK_STREAM, AF_INET, AF_INET6, \
    IPV6_V6ONLY, SOL_SOCKET, error, getaddrinfo, _socket, has_ipv6
try:
    from socket import IPPROTO_IPV6
except ImportError:  # pragma: no cover
    pass
try:
    from socket import SO_REUSEADDR
except ImportError:  # pragma: no cover
    pass
try:
    from socket import SO_REUSEPORT
except ImportError:  # pragma: no cover
    pass
try:
    from socket import has_dualstack_ipv6
except ImportError:  # pragma: no cover
    pass
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
                elif err == errno.EISCONN:  # pragma: no cover
                    # the errors on Windows are slightly different and
                    # sometimes a socket is connected but still returns
                    # EWOULDBLOCK, so here we silence the error from a
                    # second connect call
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


# The create_connection and create_server functions below are identical copies
# to those in the Python 3.8. They are included here to ensure they
# instantiate the green versions of the socket class.

def create_connection(address, timeout=_GLOBAL_DEFAULT_TIMEOUT,
                      source_address=None):  # pragma: no cover
    """Connect to *address* and return the socket object.
    Convenience function.  Connect to *address* (a 2-tuple ``(host,
    port)``) and return the socket object.  Passing the optional
    *timeout* parameter will set the timeout on the socket instance
    before attempting to connect.  If no *timeout* is supplied, the
    global default timeout setting returned by :func:`getdefaulttimeout`
    is used.  If *source_address* is set it must be a tuple of (host, port)
    for the socket to bind as a source address before making the connection.
    A host of '' or port 0 tells the OS to use the default.
    """

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
    """Convenience function which creates a SOCK_STREAM type socket
    bound to *address* (a 2-tuple (host, port)) and return the socket
    object.
    *family* should be either AF_INET or AF_INET6.
    *backlog* is the queue size passed to socket.listen().
    *reuse_port* dictates whether to use the SO_REUSEPORT socket option.
    *dualstack_ipv6*: if true and the platform supports it, it will
    create an AF_INET6 socket able to accept both IPv4 or IPv6
    connections. When false it will explicitly disable this option on
    platforms that enable it by default (e.g. Linux).
    >>> with create_server(('', 8000)) as server:
    ...     while True:
    ...         conn, addr = server.accept()
    ...         # handle new connection
    """
    if reuse_port and not hasattr(_socket, "SO_REUSEPORT"):
        raise ValueError("SO_REUSEPORT not supported on this platform")
    if dualstack_ipv6:
        if not has_dualstack_ipv6():
            raise ValueError("dualstack_ipv6 not supported on this platform")
        if family != AF_INET6:
            raise ValueError("dualstack_ipv6 requires AF_INET6 family")
    sock = socket(family, SOCK_STREAM)
    try:
        # Note about Windows. We don't set SO_REUSEADDR because:
        # 1) It's unnecessary: bind() will succeed even in case of a
        # previous closed socket on the same address and still in
        # TIME_WAIT state.
        # 2) If set, another socket is free to bind() on the same
        # address, effectively preventing this one from accepting
        # connections. Also, it may set the process in a state where
        # it'll no longer respond to any signals or graceful kills.
        # See: msdn2.microsoft.com/en-us/library/ms740621(VS.85).aspx
        if os.name not in ('nt', 'cygwin') and \
                hasattr(_socket, 'SO_REUSEADDR'):
            try:
                sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            except error:
                # Fail later on bind(), for platforms which may not
                # support this option.
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
