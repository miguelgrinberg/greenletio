How Is It Possible?
===================

``greenletio`` combines asynchronous functions with greenlets to achieve what
is not possible using standalone Python.

Greenlets provide a way to context-switch or "jump" from the middle of a
running function into another, and later resume the first at the place it was
interrupted.

This opens the possibility for a synchronous function that is running as a
greenlet to "escape" a blocking wait by jumping to an asynchronous function
(also running as a greenlet) that releases the CPU back to the loop and calls
``await`` on behalf of the sync function. The interrupted sync function would
then be resumed via another greenlet jump once the blocking condition is
resolved.

Previous work
-------------

The idea for ``greenletio`` originated in a proof-of-concept gist by Mike
Bayer that used greenlets to prevent synchronous code from blocking. The
intent was to use this technique to allow SQLAlchemy to work in asynchronous
applications. This technique currently allows SQLAlchemy to work with
asynchronous database drivers.

Since Mike's code became public we learned of another project combining
coroutines and greenlets with the same goal called
`greenback <https://github.com/oremanj/greenback>`_, by Joshua Oreman.

The overall design of ``greenletio`` is based on
`eventlet <https://eventlet.net>`_.
