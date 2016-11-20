import aiohttp
import asyncio
import re
import sys

_URL = "https://www.israelpost.co.il/itemtrace.nsf/trackandtraceNDJSON?openagent&lang=EN&itemcode={}"


async def _get_tracking(tracking, *, session):
    async with session.get(_URL.format(tracking)) as response:
        response.raise_for_status()
        json = await response.json()
        return re.sub(r' *<br>.*$', '', json['itemcodeinfo'])


async def _main(loop):
    trackings = sys.argv[1:]
    async with aiohttp.ClientSession(loop=loop) as session:
        results = await asyncio.gather(*(_get_tracking(tracking, session=session) for tracking in trackings),
                                       loop=loop)
        print('\n'.join('{}: {}'.format(tracking, result) for tracking, result in zip(trackings, results)))


def main():
    import logging
    logging.getLogger('aiohttp.client').setLevel(logging.ERROR)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(_main(loop))
