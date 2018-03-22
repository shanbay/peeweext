import datetime
import inspect

import peewee as pw
import pendulum
from blinker import signal
from playhouse import pool, db_url

from .validator import ModelValidator, BaseValidator, FunctionValidator

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


pre_save = signal('pre_save')
post_save = signal('post_save')
pre_delete = signal('pre_delete')
post_delete = signal('post_delete')
pre_init = signal('pre_init')


_MODEL_VALIDATOR_NAME = '_validator'
_CUSTOM_MODEL_VALIDATOR_PREFIX = 'validate_'


class ModelMeta(pw.ModelBase):
    """Overwrite peewee`s Model meta class, provide validation."""
    # store all model`s custom validators,
    # eg: {`model`: {`filed_name`: `validator`}}
    CUSTOM_VALIDATORS = {}

    def __init__(cls, name, bases, attrs):
        """Add model validator and convert validation method to validator"""
        super().__init__(name, bases, attrs)
        if name == pw.MODEL_BASE or bases[0].__name__ == pw.MODEL_BASE:
            pass
        else:
            # create ModelValidator
            model_validator = ModelValidator(cls)
            setattr(cls, _MODEL_VALIDATOR_NAME, model_validator)
            custom_validators = {}  # eg: {'field_name': `validator`}
            # add base class`s custom validation function
            for base in bases:
                if base in ModelMeta.CUSTOM_VALIDATORS:
                    custom_validators.update(ModelMeta.CUSTOM_VALIDATORS[base])
            # add custom validator by model`s validation method
            for k, v in attrs.items():
                if (k.startswith(_CUSTOM_MODEL_VALIDATOR_PREFIX) and
                        (inspect.isfunction(v) or
                            (isinstance(v, list) and
                             isinstance(v[0], BaseValidator)))):
                    field_name = k.replace(_CUSTOM_MODEL_VALIDATOR_PREFIX, '')
                    if field_name not in cls._meta.fields:
                        continue
                    if not isinstance(v, list):
                        # replace method with validator
                        v = FunctionValidator(v)
                        setattr(cls, k, v)
                    custom_validators[field_name] = v

            # add all validation to ModelValidator
            for k, v in custom_validators.items():
                if isinstance(v, list):
                    for i in reversed(v):
                        model_validator.add_validator(k, i)
                else:
                    model_validator.add_validator(k, v)

            # record to base model`s validators map
            ModelMeta.CUSTOM_VALIDATORS[cls] = custom_validators


class Model(pw.Model, metaclass=ModelMeta):
    created_at = DatetimeTZField(default=pendulum.utcnow)
    updated_at = DatetimeTZField(default=pendulum.utcnow)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        pre_init.send(type(self), instance=self)

    def save(self, *args, **kwargs):
        self.validate()

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

    def validate(self):
        getattr(self, _MODEL_VALIDATOR_NAME).validate(self)


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
