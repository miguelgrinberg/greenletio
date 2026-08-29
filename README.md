# greenletio

[![tests](https://code.miguelgrinberg.com/miguelgrinberg/greenletio/badges/workflows/tests.yml/badge.svg)](https://code.miguelgrinberg.com/miguelgrinberg/greenletio/actions)

This project allows synchronous and asynchronous functions to be used together.
Unlike other methods based on executors and thread or process pools,
`greenletio` allows synchronous functions to work like their asynchronous
counterparts, without the need to create expensive threads or processes.

## Examples

The following are some of the possibilities when using `greenletio`.

### Convert a sync function into an awaitable

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

### Use await inside a sync function

```python
from greenletio import await_

async def async_function():
    pass

def sync_function():
    await_(async_function())
```

### Call an async function as a normal function

```python
from greenletio import await_

@await_
async def async_function():
    pass

def sync_function():
    async_function()
```

## Resources

- [git](https://code.miguelgrinberg.com/miguelgrinberg/greenletio)
- [Change Log](https://code.miguelgrinberg.com/miguelgrinberg/greenletio/src/branch/main/CHANGES.md)
- [Documentation](https://greenletio.readthedocs.io/)
- [PyPI](https://pypi.python.org/pypi/greenletio)
- [Contributor's guide](CONTRIBUTING.md)
- [Security policy](SECURITY.md)

Sponsor this project
--------------------

This project relies on contributions from its users. If you benefit from it please consider making a single or ongoing monetary contribution in one of the following platforms:

- [Github Sponsors](https://github.com/sponsors/miguelgrinberg)
- [Patreon](https://patreon.com/miguelgrinberg)
- [Buy me a Coffee](https://buymeacoffee.com/miguelgrinberg)
- [thanks.dev](https://thanks.dev/u/gh/miguelgrinberg)
- [PayPal](https://paypal.me/miguelgrinberg)

Thank you!
