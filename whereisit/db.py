from contextlib import closing, contextmanager
from pony import orm

db = orm.Database()

class Tracking(db.Entity):
    id = orm.PrimaryKey(str)
    status = orm.Optional(str)
