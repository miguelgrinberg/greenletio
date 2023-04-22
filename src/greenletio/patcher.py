from contextlib import contextmanager
import sys

patched = {}


def copy_globals(source_module, globals_dict):
    for attr in dir(source_module):
        if not getattr(globals_dict, attr, None):
            globals_dict[attr] = getattr(source_module, attr)


@contextmanager
def patch_blocking(modules=None):
    """Context manager that replaces blocking modules from the Python standard
    library with non-blocking replacements.

    The following example shows how to import the ``requests`` package so that
    it becomes non-blocking::

        with patch_blocking():
            import requests

    :param modules: the list of modules to patch, or `None` to patch all the
                    supported modules, which at this time are ``socket``,
                    ``select``, ``selectors``, ``ssl``, ``threading`` and
                    ``time``.
    """
    saved = {}
    saved_module_list = list(sys.modules.keys()).copy()
    if modules is None:
        modules = ['socket', 'select', 'selectors', 'ssl', 'threading', 'time']
    for module in modules:
        if module not in patched:
            patched[module] = getattr(
                __import__('greenletio.green.' + module).green, module)
    if '__greenletio_patched__' not in sys.modules:
        for module in modules:
            if module in sys.modules:
                saved[module] = sys.modules[module]
            sys.modules[module] = patched[module]
        sys.modules['__greenletio_patched__'] = True
    yield
    for module in saved:
        sys.modules[module] = saved[module]
    for module in list(sys.modules.keys()).copy():
        if module not in saved_module_list:
            del sys.modules[module]


def patch_psycopg2():
    """Patch the ``psycopg2`` package so that it becomes non-blocking."""
    import psycopg2
    from psycopg2.extensions import POLL_OK, POLL_READ, POLL_WRITE
    from greenletio.io import wait_to_read, wait_to_write

    if not hasattr(psycopg2.extensions,
                   'set_wait_callback'):  # pragma: no cover
        raise ImportError(
            "support for coroutines not available in this Psycopg version (%s)"
            % psycopg2.__version__)

    def psycopg2_wait_callback(conn):  # pragma: no cover
        fd = conn.fileno()
        while True:
            state = conn.poll()
            if state == POLL_OK:
                break
            elif state == POLL_READ:
                wait_to_read(fd)
            elif state == POLL_WRITE:
                wait_to_write(fd)
            else:
                raise psycopg2.OperationalError(
                    "Bad result from poll: %r" % state)

    psycopg2.extensions.set_wait_callback(psycopg2_wait_callback)
