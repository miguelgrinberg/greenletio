import errno
from greenletio.io import wait_to_read, wait_to_write
from greenletio.patcher import copy_globals
import socket as __original_socket

copy_globals(__original_socket, globals())


class socket(__original_socket.socket):
    def _nonblocking_read(self, method, *args, **kwargs):
        self.setblocking(False)
        while True:
            try:
                ret = method(*args, **kwargs)
            except (OSError, BlockingIOError) as exc:
                err = exc.errno
                if err in (errno.EAGAIN, errno.EWOULDBLOCK, errno.EINPROGRESS):
                    wait_to_read(self.fileno())
                else:
                    raise
            else:
                break
        return ret

    def _nonblocking_write(self, method, *args, **kwargs):
        self.setblocking(False)
        while True:
            try:
                ret = method(*args, **kwargs)
            except (OSError, BlockingIOError) as exc:
                err = exc.errno
                ret = None
                if err in (errno.EAGAIN, errno.EWOULDBLOCK, errno.EINPROGRESS):
                    wait_to_write(self.fileno())
                    if err == errno.EINPROGRESS:
                        break
                else:
                    raise
            else:
                break
        return ret

    def accept(self, *args, **kwargs):
        wait_to_read(self.fileno())
        conn, address = self._nonblocking_read(super().accept, *args, **kwargs)
        conn.setblocking(False)
        fd = conn.detach()
        return socket(fileno=fd), address

    def connect(self, *args, **kwargs):
        return self._nonblocking_write(super().connect, *args, **kwargs)

    def connect_ex(self, *args, **kwargs):
        return self._nonblocking_write(super().connect_ex, *args, **kwargs)

    def recv(self, *args, **kwargs):
        return self._nonblocking_read(super().recv, *args, **kwargs)

    def recvfrom(self, *args, **kwargs):
        return self._nonblocking_read(super().recvfrom, *args, **kwargs)

    def recvmsg(self, *args, **kwargs):
        return self._nonblocking_read(super().recvmsg, *args, **kwargs)

    def recvmsg_into(self, *args, **kwargs):
        return self._nonblocking_read(super().recvmsg_into, *args, **kwargs)

    def recvfrom_into(self, *args, **kwargs):
        return self._nonblocking_read(super().recvfrom_into, *args, **kwargs)

    def recv_into(self, *args, **kwargs):
        return self._nonblocking_read(super().recv_into, *args, **kwargs)

    def send(self, *args, **kwargs):
        return self._nonblocking_write(super().send, *args, **kwargs)

    def sendall(self, *args, **kwargs):
        return self._nonblocking_write(super().sendall, *args, **kwargs)

    def sendto(self, *args, **kwargs):
        return self._nonblocking_write(super().sendto, *args, **kwargs)

    def sendmsg(self, *args, **kwargs):
        return self._nonblocking_write(super().sendmsg, *args, **kwargs)

    def sendmsg_afalg(self, *args, **kwargs):
        return self._nonblocking_write(super().sendmsg_afalg, *args, **kwargs)

    def sendfile(self, *args, **kwargs):
        return self._nonblocking_write(super().sendfile, *args, **kwargs)
