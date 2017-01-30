import aiohttp
import asyncio
import contextlib
import re
import sys
import toml
import uvloop
from pony import orm
from pathlib import Path
from .db import db, Tracking
from .exceptions import PostOfficeError
from .html_stripper import HTMLStripper
from .mailgun import Mailgun


class Tracker:
    INTERVAL = 60*60

    def __init__(self, *, loop, db, config):
        super().__init__()
        self._loop = loop
        self._db = db
        self._config = config
        self._next_call = self._loop.time()

    def _schedule_next_call(self):
        self._next_call += self.INTERVAL
        self._loop.call_at(self._next_call, self._loop.create_task, self.run())

    async def _get_tracking(self, tracking, *, session):
        url = f'https://www.israelpost.co.il/itemtrace.nsf/trackandtraceNDJSON?openagent&lang=EN&itemcode={tracking}'
        async with session.get(url) as response:
            response.raise_for_status()
            json = await response.json()
            if not json['typename']:
                raise PostOfficeError(tracking, json)
            stripper = HTMLStripper()
            stripper.feed(json['itemcodeinfo'])
            return tracking, stripper.get_data()

    async def run(self):
        self._schedule_next_call()

        trackings = self._config['trackings']
        async with aiohttp.ClientSession() as session:
            mail = Mailgun(session=session, domain=self._config['mailgun']['domain'],
                           api_key=self._config['mailgun']['api_key'])
            futures = asyncio.as_completed([self._get_tracking(tracking, session=session) for tracking in trackings])
            mails = []
            with orm.db_session():
                for future in futures:
                    try:
                        tracking_id, status = await future
                    except PostOfficeError as e:
                        print(e)
                        continue
                    print(f'{tracking_id}: {status}')

                    tracking = orm.get(t for t in Tracking if t.id == tracking_id)
                    if not tracking:
                        tracking = Tracking(id=tracking_id)
                        self._db.commit()

                    if tracking.status != status:
                        mails.append(mail.send(
                            from_addr=self._config['mailgun']['from'],
                            to_addrs=self._config['mailgun']['to'],
                            subject=f'Your {self._config["trackings"][tracking_id]} is getting closer',
                            body=f'{tracking_id}: {status}'))
                        tracking.status = status

            if mails:
                await asyncio.wait(mails)


def main():
    config_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / '.config' / 'whereisit.toml'
    with open(config_path) as f:
        config = toml.load(f)

    import logging
    logging.getLogger('aiohttp.client').setLevel(logging.ERROR)

    db_path = Path.home() / '.local' / 'share' / config['database']['path']
    orm.sql_debug(config['database'].get('debug', False))
    db.bind("sqlite", str(db_path), create_db=True)
    db.generate_mapping(create_tables=True)

    with orm.db_session():
        orm.select(t for t in db.Tracking
                   if t.id not in list(config['trackings'].keys())).delete(bulk=True)

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    with contextlib.closing(asyncio.get_event_loop()) as loop:
        tracker = Tracker(loop=loop, db=db, config=config)
        loop.create_task(tracker.run())
        loop.run_forever()
