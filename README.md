# greenletio

[![Build status](https://github.com/miguelgrinberg/greenletio/workflows/build/badge.svg)](https://github.com/miguelgrinberg/greenletio/actions) [![codecov](https://codecov.io/gh/miguelgrinberg/greenletio/branch/main/graph/badge.svg)](https://codecov.io/gh/miguelgrinberg/greenletio)

This project allows synchronous and asynchronous functions to be used together.
Unlike other methods based on executors and thread or process pools,
`greenletio` allows synchronous functions to work like their asynchronous
counterparts, without the need to create expensive threads or processes.

## Quick start

### Installation

This package is installed with `pip`:

```
$ pip install greenletio
```

### async_

The `async_` function makes a synchronous function awaitable.

```python
import asyncio
from greenletio import async_

def sync_function(arg):
    pass

async def async_function():
    await async_(sync_function)(42)

asyncio.run(async_function())
```

This function can also be used as a decorator:

```python
import asyncio
from greenletio import async_

@async_
def sync_function(arg):
    pass

async def async_function():
    await sync_function(42)

asyncio.run(async_function())
```

### await_

The `await_` function can be used to await an asynchronous function in a
synchronous one without blocking the asyncio loop:

```python
from greenletio import await_

async def async_function():
    pass

def sync_function():
    await_(async_function())
```

Sometimes it is more convenient to use `await_` as a decorator to make an
asynchronous function callable from synchronous code (once again, without
blocking the loop):

```python
from greenletio import await_

@await_
async def async_function():
    pass

def sync_function():
    async_function()
```

Note that synchronous functions used in asynchronous applications must follow
the rules that apply to asynchronous functions with regards to not calling any
blocking code.

### spawn

The `spawn` function launches a synchronous Python function asynchronously as
a greenlet. The new greenlet (and any function called from it) can use the
`await_` function.

### green.*

The modules under `greenletio.green` are drop-in replacements of the Python
standard library modules of the same name, implemented using the `async_`,
`await_` and `spawn` primitives.

The goal is to provide replacements for all the blocking functions in the
standard library, so that code written as blocking can be used asynchronously.

Currently implemented modules are `socket`, `ssl`, `threading`, and
`time`.

### patch_blocking

The `patch_blocking` context manager can be used to import code written for
the Python standard library with all the blocking functions redirected to
their `green.*` replacements.

### patch_psycopg2

The `patch_psycopg2` function configures psycopg2 to access Postgres database
in non-blocking mode.

## Why?

Porting an application to asyncio is in general very complicated, as it
requires a large portion of the codebase to be converted due to the "virality"
of asynchronous code, which requires that only an asynchronous function call
another asynchronous function.

This package provides a solution to allow synchronous and asynchronous code to
call each other without blocking the asynchronous loop.

## How is this possible?

`greenletio` combines asynchronous functions with
[greenlets](https://greenlet.readthedocs.io/en/latest/) to achieve what is not
possible using standalone Python.

Greenlets provide a way to context-switch or "jump" from the middle of a
running function into another, and later resume the first at the place it was
interrupted.

This opens the possibility for a synchronous function to "escape" a blocking
wait by context-switching into an asynchronous function that releases the CPU
back to the loop. The interrupted function would only be resumed once the
blocking condition is resolved.

## Previous work

The idea for `greenletio` originated in a
[proof-of-concept gist](https://gist.github.com/zzzeek/4e89ce6226826e7a8df13e1b573ad354)
by Mike Bayer that used greenlets to prevent synchronous code from blocking.
The intent was to use this technique to allow SQLAlchemy to work in
asynchronous applications.

Since Mike's code became public we learned of another project combining
coroutines and greenlets with the same goal called
[greenback](https://github.com/oremanj/greenback), by Joshua Oreman.

The overall design of `greenletio` is based on [eventlet](https://eventlet.net/).
