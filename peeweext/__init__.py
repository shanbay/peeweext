from threading import Lock
import peewee as pw
from playhouse.db_url import connect, register_database
from playhouse import pool


__version__ = '0.1.0'


class cached_property:
    """ thread safe cached property """

    def __init__(self, func, name=None):
        self.func = func
        self.__doc__ = getattr(func, '__doc__')
        self.name = name or func.__name__
        self.lock = Lock()

    def __get__(self, instance, cls=None):
        with self.lock:
            if instance is None:
                return self
            try:
                return instance.__dict__[self.name]
            except KeyError:
                res = instance.__dict__[self.name] = self.func(instance)
                return res


class Peeweext:

    def __init__(self, ns='PW_'):
        self.ns = ns

    def init_app(self, app):
        config = app.config.get_namespace(self.ns)
        conn_params = config.get('conn_params', {})
        self.database = connect(config['db_url'], **conn_params)
        self.model_class = config.get('model', pw.Model)

    @cached_property
    def Model(self):
        class BaseModel(self.model_class):
            class Meta:
                database = self.database
        return BaseModel

    def __getattr__(self, name):
        return getattr(self.database, name)


class SmartDatabase:

    """
    if you use transaction, you must use it in a connection context explict:

    with db.connection_context():
        with db.atomic() as transaction:
            pass
    """

    def execute(self, *args, **kwargs):
        if self.in_transaction():
            return super().execute(*args, **kwargs)
        with self.connection_context():
            return super().execute(*args, **kwargs)


_smarts = {
    'SmartMySQLDatabase': ['mysql+smart'],
    'SmartPostgresqlDatabase': ['postgres+smart', 'postgresql+smart'],
    'SmartPostgresqlExtDatabase': ['postgresext+smart', 'postgresqlext+smart'],
    'SmartSqliteDatabase': ['sqlite+smart'],
    'SmartSqliteExtDatabase': ['sqliteext+smart'],
    'SmartCSqliteExtDatabase': ['csqliteext+smart']
}

for n, urls in _smarts.items():
    pc = getattr(pool, 'Pooled{}'.format(n[5:]))
    if pc is not None:
        smart_cls = type(n, (SmartDatabase, pc), {})
        register_database(smart_cls, *urls)
        globals()[n] = smart_cls
