from werkzeug.utils import import_string, cached_property
from playhouse import db_url

from peeweext.proxy import Proxy


class UninitializedException(Exception):
    pass


class Peeweext:
    def __init__(self, ns='PW_'):
        self.ns = ns
        self._database = None
        # make a connection pool proxy
        self.database = Proxy(self._get_db)

    def init_app(self, app):
        config = app.config.get_namespace(self.ns)
        self.model_class = import_string(
            config.get('model', 'peeweext.model.Model'))
        conn_params = config.get('conn_params', {})

        # initialize private connection pool
        self._database = db_url.connect(config['db_url'], **conn_params)

        self._register_handlers(app)

    def _get_db(self):
        if not self._database:
            raise UninitializedException()
        return self._database

    @cached_property
    def Model(self):
        class BaseModel(self.model_class):
            class Meta:
                # 为什么这里不直接使用当前实例的_database而是用了proxy？
                # 是为了使Meta.database始终和实例的_database保持一致
                database = Proxy(self._get_db)

        return BaseModel

    def connect_db(self):
        if self.database.is_closed():
            self.database.connect()

    def close_db(self, exc):
        if not self.database.is_closed():
            self.database.close()

    def _register_handlers(self, app):
        app.before_request(self.connect_db)
        app.teardown_request(self.close_db)
        try:
            from celery.signals import task_prerun, task_postrun
            task_prerun.connect(
                lambda *arg, **kw: self.connect_db(), weak=False)
            task_postrun.connect(
                lambda *arg, **kw: self.close_db(None), weak=False)
        except ImportError:
            pass
