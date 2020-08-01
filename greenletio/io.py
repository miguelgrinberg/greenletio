from greenlet import getcurrent
from greenletio.core import bridge


def _reader_callback(fd, gl):
    bridge.loop.remove_reader(fd)
    bridge.schedule(gl)


def _writer_callback(fd, gl):
    bridge.loop.remove_writer(fd)
    bridge.schedule(gl)


def wait_to_read(fd):
    if not bridge.running and not bridge.starting:  # pragma: no cover
        bridge.start()
    bridge.loop.add_reader(fd, _reader_callback, fd, getcurrent())
    bridge.switch()


def wait_to_write(fd):
    if not bridge.running and not bridge.starting:  # pragma: no cover
        bridge.start()
    bridge.loop.add_writer(fd, _writer_callback, fd, getcurrent())
    bridge.switch()
