Quick Start
-----------

Installation
~~~~~~~~~~~~

This package is installed with ``pip``::

 pip install greenletio

``async_``
~~~~~~~~~~

The ``async_`` function makes a synchronous function awaitable::

 import asyncio
 from greenletio import async_

 def sync_function(arg):
     pass

 async def async_function():
     await async_(sync_function)(42)

 asyncio.run(async_function())

This function can also be used as a decorator::

 import asyncio
 from greenletio import async_

 @async_
 def sync_function(arg):
     pass

 async def async_function():
     await sync_function(42)

 asyncio.run(async_function())

``await_``
~~~~~~~~~~

The ``await_`` function can be used to await an asynchronous function in a
synchronous one, without blocking the asyncio loop::

 from greenletio import await_

 async def async_function():
     pass

 def sync_function():
     await_(async_function())

Sometimes it is more convenient to use ``await_`` as a decorator to make an
asynchronous function callable from synchronous code (once again, without
blocking the loop)::

 from greenletio import await_

 @await_
 async def async_function():
     pass

 def sync_function():
     async_function()

Note that synchronous functions used in asynchronous applications must follow
the rules that apply to asynchronous functions with regards to not calling any
blocking code.

``spawn``
~~~~~~~~~

The ``spawn`` function launches a synchronous Python function asynchronously
as a greenlet. The new greenlet (and any function called from it) can use the
``await_`` function.

``green.*``
~~~~~~~~~~~

The modules under ``greenletio.green`` are drop-in replacements of the Python
standard library modules of the same name, implemented using the ``async_``,
``await_`` and ``spawn`` primitives.

The goal is to provide replacements for commonly used blocking functions in
the standard library, so that code written in blocking style can be used
asynchronously.

Currently implemented modules are ``socket``, ``ssl``, ``threading``, and
``time``.

``patch_blocking``
~~~~~~~~~~~~~~~~~~

The ``patch_blocking`` context manager can be used to import code written for
the Python standard library with all the blocking functions redirected to
their ``green.*`` replacements.

``patch_psycopg2``
~~~~~~~~~~~~~~~~~~

The ``patch_psycopg2`` function configures psycopg2 to access  Postgres
databases in non-blocking mode.
