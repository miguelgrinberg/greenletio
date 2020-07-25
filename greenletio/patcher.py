from contextlib import contextmanager
import sys

patched = {}


def copy_globals(source_module, globals_dict):
    for attr in dir(source_module):
        if not getattr(globals_dict, attr, None):
            globals_dict[attr] = getattr(source_module, attr)


@contextmanager
def patch_blocking(modules=None):
    if modules is None:
        modules = ['socket', 'ssl']
    for module in modules:
        if module not in patched:
            patched[module] = getattr(
                __import__('greenletio.green.' + module).green, module)
    if '__greenletio_patched__' in sys.modules:
        # recursive patching
        yield
        return

    saved = {}
    for module in modules:
        saved[module] = sys.modules[module]
        sys.modules[module] = patched[module]
    sys.modules['__greenletio_patched__'] = True
    yield
    for module in modules:
        sys.modules[module] = saved[module]
    del sys.modules['__greenletio_patched__']
