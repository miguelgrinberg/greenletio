"""
Source: https://gist.github.com/zzzeek/4e89ce6226826e7a8df13e1b573ad354

This program is exactly the same as that of
https://gist.github.com/zzzeek/33943060f7a08cf9e82bf8df1f0f75de ,
with the exception that the add_and_select_data function is written in
synchronous style.

UPDATED!!   now includes refinements by @snaury and @Caselit .  SIMPLER
AND FASTER!!


Instead of the "await" keyword, we use the "await_()" function to interact with
the greenlet context. the greenlet context itself is 23 lines of code right
here.

See also https://gist.github.com/zzzeek/769b684d4fc8dfec9d4ebc6e4bb93076 for
an even simpler version of the greenlet switch.

Performance against a PG database over a wired network is now essentially
THE SAME as raw asyncio

Ran 40000 records in 40 concurrent requests, Total time 5.517673
"""

import asyncio
import random
import sys

import asyncpg
import greenlet


def await_(coroutine):
    current = greenlet.getcurrent()

    if not isinstance(current, AsyncIoGreenlet):
        raise Exception(
            "not running inside a greenlet right now, "
            "can't use await_() function"
        )

    return current.driver.switch(coroutine)


class AsyncIoGreenlet(greenlet.greenlet):
    def __init__(self, driver, fn):
        greenlet.greenlet.__init__(self, fn, driver)
        self.driver = driver


async def greenlet_spawn(__fn, *args, **kw):
    target = AsyncIoGreenlet(greenlet.getcurrent(), __fn)

    target_return = target.switch(*args, **kw)

    while target:
        try:
            result = await target_return
        except:
            target_return = target.throw(*sys.exc_info())
        else:
            target_return = target.switch(result)

    # clean up cycle for the common case
    # (gc can do the exception case)
    del target.driver
    return target_return


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
                user="postgres",
                password="postgres",
                host="localhost",
                database="test",
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
                user="postgres",
                password="postgres",
                host="localhost",
                database="test",
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
