import json
import datetime
import peewee as pw
import pendulum


pw.MySQLDatabase.field_types.update({'DATETIME': 'DATETIME(6)'})
pw.PostgresqlDatabase.field_types.update({'DATETIME': 'TIMESTAMPTZ'})


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
        if value is None:
            return value
        data = json.dumps(value)
        if len(data) > self.max_length:
            raise ValueError('Data too long for field {}.'.format(self.name))
        return data

    def python_value(self, value):
        if value is None:
            return value
        return json.loads(value)
