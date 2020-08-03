Postgres Benchmark
==================

This test was created by Mike Bayer to evaluate database performance of
different asynchronous solutions. Mike's own implementations are based on the
`asyncpg` Postgres driver. I have written a `greenletio` version of this test,
as well as additional implementations with the psycopg2 package.

All the tests expect a Postgres database named `test` running in `localhost`,
with access to user `postgress` with password `postgres`.
