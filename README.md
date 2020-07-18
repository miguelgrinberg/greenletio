# greenletio

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

The idea for `greenbackio` originated in a
[proof-of-concept example](https://gist.github.com/zzzeek/4e89ce6226826e7a8df13e1b573ad354)
that used greenlets to prevent synchronous code from blocking by Mike Bayer,
with the intent of applying this technique to allow SQLAlchemy to work in
asynchronous applications.

Since Mike's code became public we learned of another project combining
coroutines and greenlets with the same goal called
[greenback](https://github.com/oremanj/greenback), by Joshua Oreman.
