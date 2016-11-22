import aiohttp
import asyncio
import os
import re
import shelve
import sys
import toml
from .mailgun import Mailgun

_URL = 'https://www.israelpost.co.il/itemtrace.nsf/trackandtraceNDJSON?openagent&lang=EN&itemcode={}'


async def _get_tracking(tracking, *, session):
    async with session.get(_URL.format(tracking)) as response:
        response.raise_for_status()
        json = await response.json()
        return tracking, re.sub(r' *<br>.*$', '', json['itemcodeinfo'])


async def _main(*, db, config):
    trackings = config['trackings']
    async with aiohttp.ClientSession() as session:
        mail = Mailgun(session=session, domain=config['mailgun']['domain'], api_key=config['mailgun']['api_key'])
        futures = asyncio.as_completed([_get_tracking(tracking, session=session) for tracking in trackings])
        mails = []
        for future in futures:
            tracking, status = await future
            if db.get(tracking) != status:
                mails.append(mail.send(
                    from_addr=config['mailgun']['from'],
                    to_addrs=config['mailgun']['to'],
                    subject='Your {} is getting closer'.format(config['trackings'][tracking]),
                    body='{}: {}'.format(tracking, status)))

            db[tracking] = status

        if mails:
            await asyncio.wait(mails)


def main():
    config_path = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser('~/.config/whereisit.toml')
    with open(config_path) as f:
        config = toml.load(f)

    import logging
    logging.getLogger('aiohttp.client').setLevel(logging.ERROR)

    db_path = os.path.join(os.path.expanduser('~/.local/share'), config['config']['database'])
    with shelve.open(db_path) as db:
        trackings = set(config['trackings'].keys())
        saved_packages = set(db.keys())

        for package in saved_packages - trackings:
            del db[package]

        loop = asyncio.get_event_loop()
        loop.run_until_complete(_main(db=db, config=config))
