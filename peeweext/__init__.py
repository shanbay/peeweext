import json
import datetime
import inspect

import peewee as pw
import pendulum
from blinker import signal
from playhouse import pool, db_url

from .validator import ValidateError

__version__ = '0.5.0'

try:
    from sea.utils import import_string, cached_property
except ImportError:
    from werkzeug import import_string, cached_property


class Peeweext:

    def __init__(self, ns='PW_'):
        self.ns = ns

    def init_app(self, app):
        config = app.config.get_namespace(self.ns)
        conn_params = config.get('conn_params', {})
        self.database = db_url.connect(config['db_url'], **conn_params)
        self.model_class = import_string(config.get('model', 'peeweext.Model'))

    @cached_property
    def Model(self):
        class BaseModel(self.model_class):
            class Meta:
                database = self.database

        return BaseModel


class DatetimeTZField(pw.Field):
    field_type = 'DATETIME'

    def python_value(self, value):
        if isinstance(value, str):
            return pendulum.parse(value)
        if isinstance(value, datetime.datetime):
            return pendulum.instance(value)
        return value

    def db_value(self, value):
        if value is None:
            return value
        if not isinstance(value, datetime.datetime):
            raise ValueError('datetime instance required')
        if value.utcoffset() is None:
            raise ValueError('timezone aware datetime required')
        if isinstance(value, pendulum.Pendulum):
            value = value._datetime
        return value.astimezone(datetime.timezone.utc)


class JSONCharField(pw.CharField):
    def db_value(self, value):
        return json.dumps(value)

    def python_value(self, value):
        return json.loads(value)


pre_save = signal('pre_save')
post_save = signal('post_save')
pre_delete = signal('pre_delete')
post_delete = signal('post_delete')
pre_init = signal('pre_init')


class ModelMeta(pw.ModelBase):
    """Model meta class, provide validation."""

    def __init__(cls, name, bases, attrs):
        """Store validator."""
        super().__init__(name, bases, attrs)
        validators = {}  # {'field_name': `callable`}
        setattr(cls, '_validators', validators)
        # add validator by model`s validation method
        for k, v in attrs.items():
            if k.startswith('validate_') and inspect.isfunction(v):
                field_name = k[9:]  # 9 = len('validate_')
                if field_name not in cls._meta.fields:
                    continue
                validators[field_name] = v


class Model(pw.Model, metaclass=ModelMeta):
    created_at = DatetimeTZField(default=pendulum.utcnow)
    updated_at = DatetimeTZField(default=pendulum.utcnow)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        pre_init.send(type(self), instance=self)
        self._validate_errors = {}  # eg: {'field_name': 'error information'}

    def save(self, *args, skip_validation=False, **kwargs):
        if not skip_validation:
            if not self.is_valid:
                raise ValidateError(str(self._validate_errors))

        pk_value = self._pk
        created = kwargs.get('force_insert', False) or not bool(pk_value)
        pre_save.send(type(self), instance=self, created=created)
        ret = super().save(*args, **kwargs)
        post_save.send(type(self), instance=self, created=created)
        return ret

    def delete_instance(self, *args, **kwargs):
        pre_delete.send(type(self), instance=self)
        ret = super().delete_instance(*args, **kwargs)
        post_delete.send(type(self), instance=self)
        return ret

    def _validate(self):
        """Validate model data and save errors
        """
        errors = {}

        for name, validator in self._validators.items():
            value = getattr(self, name)

            try:
                validator(self, value)
            except ValidateError as e:
                errors[name] = str(e)

        self._validate_errors = errors

    @property
    def errors(self):
        self._validate()
        return self._validate_errors

    @property
    def is_valid(self):
        if self.errors:
            return False
        else:
            return True


def _touch_model(sender, instance, created):
    if issubclass(sender, Model):
        instance.updated_at = pendulum.utcnow()


pre_save.connect(_touch_model)
pw.MySQLDatabase.field_types.update({'DATETIME': 'DATETIME(6)'})
pw.PostgresqlDatabase.field_types.update({'DATETIME': 'TIMESTAMPTZ'})


class SmartDatabase:
    """
    if you use transaction, you must wrap it with a connection context explict:

    with db.connection_context():
        with db.atomic() as transaction:
            pass

    **notice**: if you use nested transactions, only wrap the most outside one
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
        db_url.register_database(smart_cls, *urls)
        globals()[n] = smart_cls
