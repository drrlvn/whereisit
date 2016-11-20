import aiohttp
import asyncio
import os
import re
import shelve
import sys
import toml

_URL = 'https://www.israelpost.co.il/itemtrace.nsf/trackandtraceNDJSON?openagent&lang=EN&itemcode={}'


async def _get_tracking(tracking, *, session):
    async with session.get(_URL.format(tracking)) as response:
        response.raise_for_status()
        json = await response.json()
        return re.sub(r' *<br>.*$', '', json['itemcodeinfo'])


async def _main(*, loop, db, trackings):
    async with aiohttp.ClientSession(loop=loop) as session:
        results = await asyncio.gather(*(_get_tracking(tracking, session=session) for tracking in trackings),
                                       loop=loop)
        for tracking, status in zip(trackings, results):
            if db.get(tracking) != status:
                print('{}: {}'.format(tracking, status))
                db[tracking] = status


def main():
    config_path = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser('~/.config/whereisitrc')
    with open(config_path) as f:
        config = toml.load(f)

    import logging
    logging.getLogger('aiohttp.client').setLevel(logging.ERROR)

    with shelve.open(config['config']['database']) as db:
        trackings = set(config['trackings'].keys())
        saved_packages = set(db.keys())

        for package in (saved_packages - trackings):
            del db[package]

        loop = asyncio.get_event_loop()
        loop.run_until_complete(_main(loop=loop, db=db, trackings=config['trackings']))
