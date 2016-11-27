from contextlib import closing, contextmanager
import sqlite3


class Database:
    def __init__(self, path):
        self._path = path
        self._db = None

    def __enter__(self):
        self._db = sqlite3.connect(self._path)
        return self

    @contextmanager
    def _cursor(self, *, commit=True):
        with closing(self._db.cursor()) as c:
            yield c

        if commit:
            self._db.commit()

    def __exit__(self, *args):
        self._db.close()

    def ensure_schema(self):
        with self._cursor() as c:
            c.execute('create table if not exists trackings(id text primary key, status text)')

    def purge(self, trackings):
        with self._cursor() as c:
            c.execute('delete from trackings where id not in (?)', trackings)

    def getset(self, tracking, status):
        with self._cursor() as c:
            c.execute('select status from trackings where id=?', (tracking, ))
            row = c.fetchone()
            previous_status = None if not row else row[0]
            c.execute('insert or replace into trackings (id, status) values (?, ?)', (tracking, status))

        return previous_status
