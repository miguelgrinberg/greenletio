Purpose
=======

Porting an application written in standard Python to asyncio is in general
very complicated, as it requires a large portion of the codebase to be
converted due to the "virality" of asynchronous code, which requires that
only an asynchronous function call another asynchronous function.

This package provides a solution that allows synchronous and asynchronous code
to call each other without blocking the asynchronous loop.
