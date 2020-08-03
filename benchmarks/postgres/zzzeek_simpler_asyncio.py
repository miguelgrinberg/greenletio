"""
Source: https://gist.github.com/zzzeek/769b684d4fc8dfec9d4ebc6e4bb93076

This is a simpler version of the greenlet
example at https://gist.github.com/zzzeek/4e89ce6226826e7a8df13e1b573ad354
Instead of the "await" keyword, we use the "await_()" function to interact with
the greenlet context. the greenlet context itself is 23 lines of code right
here.
"""

import asyncio
import random
import sys

import asyncpg
import greenlet


def await_(coroutine):
    current = greenlet.getcurrent()
    parent = current.parent
    if not parent:
        raise Exception(
            "not running inside a greenlet right now, "
            "can't use await_() function"
        )

    # possibly pointless assertion
    assert parent.gr_frame.f_code is _assert_code_object

    return parent.switch(coroutine)

async def greenlet_spawn(fn, *args):

    result_future = asyncio.Future()

    def run_greenlet_target():
        result_future.set_result(fn(*args))
        return None

    async def run_greenlet():
        gl = greenlet.greenlet(run_greenlet_target)
        greenlet_coroutine = gl.switch()

        while greenlet_coroutine is not None:
            task = asyncio.create_task(greenlet_coroutine)
            try:
                await task
            except:
                # this allows an exception to be raised within
                # the moderated greenlet so that it can continue
                # its expected flow.
                greenlet_coroutine = gl.throw(*sys.exc_info())
            else:
                greenlet_coroutine = gl.switch(task.result())

    # possibly pointless assertion
    global _assert_code_object
    _assert_code_object = run_greenlet.__code__

    await run_greenlet()

    return result_future.result()


if __name__ == "__main__":

    def add_and_select_data(conn, data):
        row = await_(
            conn.fetchrow(
                "insert into mytable(data) values ($1) returning id", data
            )
        )
        id_ = row[0]
        result = await_(
            conn.fetchrow("select data from mytable where id=($1)", id_)
        )

        return result[0]

    async def setup_database():
        conn = await (
            asyncpg.connect(
                user="postgres", password="postgres", host="localhost", database="test",
            )
        )

        await (conn.execute("drop table if exists mytable"))

        await (
            conn.execute(
                "create table if not exists "
                "mytable (id serial primary key, data varchar)"
            )
        )

        await conn.close()

    concurrent_requests = 40
    num_recs = 1000

    async def run_request():
        conn = await (
            asyncpg.connect(
                user="postgres", password="postgres", host="localhost", database="test",
            )
        )

        for i in range(num_recs):
            random_data = "random %d" % (random.randint(1, 1000000))

            retval = await greenlet_spawn(
                add_and_select_data, conn, random_data
            )
            assert retval == random_data, "%s != %s" % (retval, random_data)

        await (conn.close())

    async def main():
        await setup_database()
        await asyncio.gather(
            *[run_request() for j in range(concurrent_requests)]
        )

    import time

    now = time.perf_counter()
    asyncio.run(main())
    print(
        "%f"
        % (
            (time.perf_counter() - now),
        )
    )
