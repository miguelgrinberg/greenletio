# This example shows how to use the requests library in an asynchronous
# application. The trick is to import requests with the blocking functions
# in the standard library patched, and then to convert requests functions
# into awaitables with greenletio.async_.

import asyncio
import greenletio
with greenletio.patch_blocking():
    import requests

urls = [
    'https://google.com',
    'https://microsoft.com',
    'https://apple.com',
    'https://netflix.com',
    'https://ebay.com'
]


async def req(url):
    print(f'{url}: Requesting...')
    r = await greenletio.async_(requests.get)(url)
    print(f'{url}: {r.status_code}')


async def main():
    tasks = [asyncio.create_task(req(url)) for url in urls]
    await asyncio.gather(*tasks)


asyncio.run(main())
