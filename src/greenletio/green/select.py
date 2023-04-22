from greenletio.io import wait_many
from greenletio.patcher import copy_globals
import select as _original_select_

copy_globals(_original_select_, globals())


def devpoll():  # pragma: no cover
    raise NotImplementedError("devpoll is not supported")


def epoll(sizehint=-1, flags=0):  # pragma: no cover
    raise NotImplementedError("epoll is not supported")


def poll():  # pragma: no cover
    raise NotImplementedError("poll is not supported")


def kqueue():  # pragma: no cover
    raise NotImplementedError("kqueue is not supported")


def kevent(ident, filter=0, flags=0, fflags=0, data=0,
           udata=0):  # pragma: no cover
    raise NotImplementedError("kevent is not supported")


def select(read_list, write_list, error_list, timeout=None):
    return wait_many(read_list, write_list, timeout) + ([],)
