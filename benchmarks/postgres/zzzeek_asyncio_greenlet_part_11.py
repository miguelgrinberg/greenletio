"""
Source: https://gist.github.com/zzzeek/a63254eedac043b3c233a0de5352f9c5

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

    try:
        spawning = current.spawning_greenlet
    except AttributeError:
        raise Exception(
            "not running inside a greenlet right now, "
            "can't use await_() function"
        )
    else:

        return spawning.switch(coroutine)


async def greenlet_spawn(__fn, *args, **kw):
    target = greenlet.greenlet(__fn)
    target.spawning_greenlet = greenlet.getcurrent()

    target_return = target.switch(*args, **kw)

    try:
        while True:
            if not target:
                return target_return
            task = asyncio.create_task(target_return)

            try:
                await task
            except:
                target_return = target.throw(*sys.exc_info())
            else:
                target_return = target.switch(task.result())
    finally:
        target.spawning_greenlet = None


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
