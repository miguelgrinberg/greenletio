Quick Start
-----------

Installation
~~~~~~~~~~~~

This package is installed with ``pip``::

 pip install greenletio

Converting a Regular Function to Asynchronous
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :func:`greenletio.async_` function makes a synchronous function
awaitable::

   import asyncio
   from greenletio import async_

   def sync_function(arg):
      pass

   async def async_function():
      await async_(sync_function)(42)  # <-- non-blocking function call

   asyncio.run(async_function())

The ``async_`` function can also be used as a decorator::

   import asyncio
   from greenletio import async_

   @async_
   def sync_function(arg):
      pass

   async def async_function():
      await sync_function(42)  # <-- non-blocking function call

   asyncio.run(async_function())

Functions wrapped with ``async_`` run inside a greenlet and have the ability
to await for asynchronous functions without blocking the asnycio loop.

Awaiting in regular functions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :func:`greenletio.await_` function can be used to await an asynchronous
function in a synchronous one, without blocking the asyncio loop::

   from greenletio import async_, await_

   async def async_function():
      pass

   @async_
   def sync_function():
      await_(async_function())  # <-- non-blocking await

   async def main():
      await sync_function()

   asyncio.run(main())

Sometimes it is more convenient to use ``await_`` as a decorator to make an
asynchronous function callable as a regular function from synchronous code
(once again, without blocking the loop)::

   from greenletio import async_, await_

   @await_
   async def async_function():
      pass

   @async_
   def sync_function():
      async_function()  # <-- this call is non-blocking

   async def main():
      await sync_function()

   asyncio.run(main())

The ``await_`` function can only be used from code that is running inside a
greenlet. A ``RuntimeError`` is raised if it is used directly in the asyncio
thread.

Synchronous functions used in asynchronous applications must follow the rules
that apply to asynchronous functions with regards to not calling any
blocking code. They must also use ``await_`` often to prevent blocking the
loop.

Implicit Use of a Loop
~~~~~~~~~~~~~~~~~~~~~~

To simplify some comon use cases such as unit testing, the ``await_`` function
can also be used directly in a non-asyncio application::

   import asyncio
   from greenletio import await_

   def main():
      await_(asyncio.sleep(1))

When ``await_`` is used in this way, an asyncio loop is started and managed
automatically by ``greenletio``.

Patching Blocking Functions in the Standard Libary
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :func:`greenletio.patch_blocking` context manager can be used to import
code written for the Python standard library with blocking functions
redirected to a set of non-blocking replacements::

   from greenletio import patch_blocking

   with patch_blocking():
      import requests

   async def main():
      await async_(requests.get)('http://google.com')  # non-blocking requests

   asyncio.run(main())

The modules that are currently patched are ``socket``, ``select``,
``selectors``, ``ssl``, ``threading``, and ``time``. Applications that use
blocking functions in other modules or in third-party packages will need to be
manually adapt their code to not block the asyncio loop.

Patching is achieved by replacing original modules from the standard library
with drop-in replacements imported from ``greenletio.green``. These adapted
versions of the original modules use the ``async_()`` and ``await_()``
functions and a variety of other techniques to avoid blocking the asyncio
loop.

Patching the psycopg2 module
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :func:`greenletio.patch_psycopg2` function configures the ``psycopg2``
package to access Postgres databases in non-blocking mode. This function needs
to be called once at the start of the application.

Automatic patching of Blocking Functions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``greenletio`` command-line tool can be used instead of the ``python``
command to run a standard (i.e. non-asyncio) script with blocking functions
in the Python Standard Library patched to non-blocking versions::

   greenletio myscript.py arg1 arg2

The ``-m`` option can be used to run a module::

   greenletio -m mymodule arg1 arg2

Green Functions
~~~~~~~~~~~~~~~


