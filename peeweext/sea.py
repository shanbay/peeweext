from sea.utils import import_string, cached_property
from sea.middleware import BaseMiddleware
from sea.pb2 import default_pb2
from playhouse import db_url
from peewee import DoesNotExist, DataError
import grpc

from .validation import ValidationError


class Peeweext:
    def __init__(self, ns='PW_'):
        self.ns = ns

    def init_app(self, app):
        config = app.config.get_namespace(self.ns)
        self.model_class = import_string(
            config.get('model', 'peeweext.model.Model'))
        conn_params = config.get('conn_params', {})
        self.database = db_url.connect(config['db_url'], **conn_params)
        self._try_setup_celery()

    @cached_property
    def Model(self):
        class BaseModel(self.model_class):
            class Meta:
                database = self.database

        return BaseModel

    def connect_db(self):
        if self.database.is_closed():
            self.database.connect()

    def close_db(self):
        if not self.database.is_closed():
            self.database.close()

    def _try_setup_celery(self):
        try:
            from celery.signals import task_prerun, task_postrun
            task_prerun.connect(
                lambda *arg, **kw: self.connect_db(), weak=False)
            task_postrun.connect(
                lambda *arg, **kw: self.close_db(), weak=False)
        except ImportError:
            pass


class PeeweextMiddleware(BaseMiddleware):
    def __init__(self, app, handler, origin_handler):
        super().__init__(app, handler, origin_handler)
        self.pwxs = [
            ext for n, ext in app.extensions.items()
            if isinstance(ext, Peeweext)
        ]

    def connect_db(self):
        for pwx in self.pwxs:
            pwx.connect_db()

    def close_db(self):
        for pwx in self.pwxs:
            pwx.close_db()

    def __call__(self, servicer, request, context):
        try:
            self.connect_db()
            return self.handler(servicer, request, context)
        except DoesNotExist:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details('Record Not Found')
        except (ValidationError, DataError) as e:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details(str(e))
        finally:
            self.close_db()
        return default_pb2.Empty()
