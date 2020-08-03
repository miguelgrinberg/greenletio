import eventlet
eventlet.monkey_patch()
import random
from threading import Thread
import psycopg2



if __name__ == "__main__":

    def add_and_select_data(cur, data):
        cur.execute(
            "insert into mytable(data) values (%s) returning id", (data,)
        )
        row = cur.fetchone()
        id_ = row[0]
        cur.execute("select data from mytable where id=(%s)", (id_,))
        result = cur.fetchone()

        return result[0]

    def setup_database():
        conn = psycopg2.connect(
            user="postgres", password="postgres", host="localhost", dbname="test",
        )

        cur = conn.cursor()
        cur.execute("drop table if exists mytable")

        cur.execute(
            "create table if not exists "
            "mytable (id serial primary key, data varchar)"
        )

        cur.close()
        conn.close()

    concurrent_requests = 40
    num_recs = 1000

    def run_request():
        conn = psycopg2.connect(
            user="postgres", password="postgres", host="localhost", dbname="test",
        )
        cur = conn.cursor()
        for i in range(num_recs):
            random_data = "random %d" % (random.randint(1, 1000000))

            retval = add_and_select_data(cur, random_data)
            assert retval == random_data, "%s != %s" % (retval, random_data)

        cur.close()
        conn.close()

    def main():
        setup_database()
        threads = [Thread(target=run_request) for j in range(concurrent_requests)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
    import time

    now = time.perf_counter()
    main()
    print(
        "%f"
        % (
            (time.perf_counter() - now),
        )
    )
