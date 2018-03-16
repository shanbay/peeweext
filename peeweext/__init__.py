import datetime
import peewee as pw
import pendulum
from blinker import signal
from playhouse import pool, db_url


from .validators  import ValidationError

__version__ = '0.4.0'


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


class Model(pw.Model):
    created_at = DatetimeTZField(default=pendulum.utcnow)
    updated_at = DatetimeTZField(default=pendulum.utcnow)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        pre_init.send(type(self), instance=self)

    def is_valid(self):
        """
        Validate the data of this model.
        :return: bool
        """
        return not self.errors

    @property
    def errors(self):
        if not hasattr(self, '_errors'):
            self.run_validation()
        return self._errors

    def run_validation(self):
        """
        Call the validate method and return validated data
        """
        self._errors = dict()
        self.__cleaned_data__ = {}
        self.run_validators()
        try:
            self.__cleaned_data__ = self.validate(self.__cleaned_data__)
        except ValidationError as e:
            self._errors['_general'] = e.detail

    def run_validators(self):
        for attr in self._meta.fields.keys():
            validator_key = 'validate_{}'.format(attr)
            value = getattr(self, attr)
            if hasattr(self, validator_key):
                try:
                    self.__cleaned_data__[attr] = getattr(
                        self, validator_key)(value)
                except ValidationError as e:
                    self._errors[attr] = e.detail
                continue
            self.__cleaned_data__[attr] = value

    def validate(self, data):
        return data

    @property
    def cleaned_data(self):
        return self.__cleaned_data__

    def save(self, *args, **kwargs):
        pk_value = self._pk
        created = kwargs.get('force_insert', False) or not bool(pk_value)
        pre_save.send(type(self), instance=self, created=created)
        if not self.is_valid():
            raise ValidationError(self.errors)
        self.__data__ = self.__cleaned_data__
        ret = super().save(*args, **kwargs)
        post_save.send(type(self), instance=self, created=created)
        return ret

    def delete_instance(self, *args, **kwargs):
        pre_delete.send(type(self), instance=self)
        ret = super().delete_instance(*args, **kwargs)
        post_delete.send(type(self), instance=self)
        return ret


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
