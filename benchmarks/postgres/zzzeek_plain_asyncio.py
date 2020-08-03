"""
Source: https://gist.github.com/zzzeek/33943060f7a08cf9e82bf8df1f0f75de

A plain asyncio program that uses asyncpg to run some rows into a table and
select them.
This is a "control" program which we will compare to the one which uses calls
from an implicit IO greenlet at
https://gist.github.com/zzzeek/4e89ce6226826e7a8df13e1b573ad354.
Performance against a PG database over a wired network
Ran 40000 records in 40 concurrent requests, Total time 5.560306
"""

import asyncio
import random

import asyncpg


if __name__ == "__main__":

    async def add_and_select_data(conn, data):
        row = await (
            conn.fetchrow(
                "insert into mytable(data) values ($1) returning id", data
            )
        )
        id_ = row[0]
        result = await (
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

            retval = await add_and_select_data(conn, random_data)
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
