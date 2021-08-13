import asyncio
from greenletio.core import await_


def _reader_callback(fd, ev):
    asyncio.get_event_loop().remove_reader(fd)
    ev.set()


def _writer_callback(fd, ev):
    asyncio.get_event_loop().remove_writer(fd)
    ev.set()


def wait_to_read(fd):
    async def wait():
        event = asyncio.Event()
        asyncio.get_event_loop().add_reader(fd, _reader_callback, fd, event)
        await event.wait()

    await_(wait())


def wait_to_write(fd):
    async def wait():
        event = asyncio.Event()
        asyncio.get_event_loop().add_writer(fd, _writer_callback, fd, event)
        await event.wait()

    await_(wait())
