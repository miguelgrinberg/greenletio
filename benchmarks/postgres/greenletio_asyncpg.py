import asyncio
import random
import sys

from greenletio import await_, async_
import asyncpg


if __name__ == "__main__":

    @async_
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
