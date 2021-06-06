# greenletio

[![Build status](https://github.com/miguelgrinberg/greenletio/workflows/build/badge.svg)](https://github.com/miguelgrinberg/greenletio/actions) [![codecov](https://codecov.io/gh/miguelgrinberg/greenletio/branch/main/graph/badge.svg)](https://codecov.io/gh/miguelgrinberg/greenletio)

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

- [Documentation](http://greenletio.readthedocs.io/en/latest/)
- [PyPI](https://pypi.python.org/pypi/greenletio)
- [Change Log](https://github.com/miguelgrinberg/greenletio/blob/main/CHANGES.md)

