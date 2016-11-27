import aiohttp
import asyncio
import contextlib
import os
import re
import sys
import toml
import uvloop
from .db import Database
from .mailgun import Mailgun


class Tracker:
    URL = 'https://www.israelpost.co.il/itemtrace.nsf/trackandtraceNDJSON?openagent&lang=EN&itemcode={}'
    INTERVAL = 60*60

    def __init__(self, *, loop, db_path, config):
        super().__init__()
        self._loop = loop
        self._db_path = db_path
        self._config = config
        self._next_call = self._loop.time()

    def _schedule_next_call(self):
        self._next_call += self.INTERVAL
        self._loop.call_at(self._next_call, self._loop.create_task, self.run())

    async def _get_tracking(self, tracking, *, session):
        async with session.get(self.URL.format(tracking)) as response:
            response.raise_for_status()
            json = await response.json()
            return tracking, re.sub(r' *<br>.*$', '', json['itemcodeinfo'])

    async def run(self):
        self._schedule_next_call()

        trackings = self._config['trackings']
        async with aiohttp.ClientSession() as session:
            mail = Mailgun(session=session, domain=self._config['mailgun']['domain'],
                           api_key=self._config['mailgun']['api_key'])
            futures = asyncio.as_completed([self._get_tracking(tracking, session=session) for tracking in trackings])
            mails = []
            with Database(self._db_path) as db:
                for future in futures:
                    tracking, status = await future
                    print('{}: {}'.format(tracking, status))
                    if db.getset(tracking, status) != status:
                        mails.append(mail.send(
                            from_addr=self._config['mailgun']['from'],
                            to_addrs=self._config['mailgun']['to'],
                            subject='Your {} is getting closer'.format(self._config['trackings'][tracking]),
                            body='{}: {}'.format(tracking, status)))

            if mails:
                await asyncio.wait(mails)


def main():
    config_path = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser('~/.config/whereisit.toml')
    with open(config_path) as f:
        config = toml.load(f)

    import logging
    logging.getLogger('aiohttp.client').setLevel(logging.ERROR)

    db_path = os.path.join(os.path.expanduser('~/.local/share'), config['config']['database'])
    with Database(db_path) as db:
        db.ensure_schema()
        db.purge(list(config['trackings'].keys()))

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    with contextlib.closing(asyncio.get_event_loop()) as loop:
        tracker = Tracker(loop=loop, db_path=db_path, config=config)
        loop.create_task(tracker.run())
        loop.run_forever()
