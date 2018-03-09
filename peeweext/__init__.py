import datetime
import peewee as pw
import pendulum
from blinker import signal
from playhouse import pool, db_url

__version__ = '0.3.0'

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


class SequenceModel(pw.Model):
    class Meta:
        seq_scope_field = None
        order_by = ('seq_scope_field', 'seq_field')

    id = pw.AutoField()
    # currently we only support a fixed column_name
    _sequence = pw.DoubleField(column_name='sequence', null=True)

    def save(self, force_insert=False, only=None):
        if force_insert or not bool(self._pk):
            klass = self.__class__
            max_obj = klass.select(klass.id).order_by(-klass.id).first()
            self._sequence = max_obj.id + 1 if max_obj else 1.0
        return super(SequenceModel, self).save(force_insert, only)

    @property
    def sequence(self):
        return self._sequence

    def _sequence_query(self):
        """
        query all sequence rows
        """
        klass = self.__class__
        # fields = [klass.id, klass._sequence]
        seq_scope_field = getattr(klass, self._meta.seq_scope_field)
        if seq_scope_field:
            # fields.append(seq_scope_field)
            # query = klass.select(fields).where(klass._sequence != None)
            query = klass.select().where(klass._sequence != None)
            seq_scope_field_value = getattr(self, self._meta.seq_scope_field)
            return query.where(seq_scope_field == seq_scope_field_value)
        return klass.select().where(klass._sequence != None)
        # return klass.select(fields).where(klass._sequence != None)

    def change_sequence(self, new_sequence):
        """
        :param new_sequence: 要排到第几个

        基本的排序思路是，找到要插入位置的前一个和后一个对象，把要
        拖动对象的sequence值设置成介于两个对象之间

        注意 current_sequence，new_sequence 两个变量是数组中
        的 index，与对象的 sequence 值不要混淆
        """
        if new_sequence < 1:
            raise ValueError("Sequence is not proper")  # pragma no cover

        with self._meta.database.transaction():
            klass = self.__class__
            current_sequence = self._sequence_query().where(klass._sequence <= self._sequence).count()
            if current_sequence == new_sequence:
                return

            # 拖到第一个时需要特殊处理
            if new_sequence > 1:
                instances = self._sequence_query().order_by(+klass._sequence)

                # 从后往前拖
                if current_sequence > new_sequence:
                    instances = instances[new_sequence - 2:new_sequence]
                # 从前往后拖
                else:
                    instances = instances[new_sequence - 1:new_sequence + 1]

                if not len(instances):
                    raise ValueError("Sequence is not proper")
                elif len(instances) == 1:
                    prev_seq = instances[0]._sequence
                    next_seq = prev_seq + 1
                else:
                    prev_ins, next_ins = instances
                    prev_seq, next_seq = prev_ins._sequence, next_ins._sequence
            else:
                prev_seq = 0
                next_seq = self._sequence_query().order_by(+klass._sequence).first()._sequence

            self._sequence = (prev_seq + next_seq) / 2
            self.save()

            # Sequence auto loosen
            # 不断的除以2，会导致精度丢失，当两个对象的 sequence 差过小时，全部重拍，重新生成 sequence
            if abs(prev_seq - next_seq) < 0.000001:
                collection = self._sequence_query().order_by(+klass._sequence)
                for index, instance in enumerate(collection):
                    instance._sequence = float(index + 1)
                    instance.save()


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

    def save(self, *args, **kwargs):
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
