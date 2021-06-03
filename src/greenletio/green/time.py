import asyncio
from greenletio.core import await_
from greenletio.patcher import copy_globals
import time as _original_time_

copy_globals(_original_time_, globals())


def sleep(seconds):  # pragma: no cover
    await_(asyncio.sleep(seconds))
