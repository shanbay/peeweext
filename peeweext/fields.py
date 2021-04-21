import json
import datetime
import peewee as pw
import pendulum


def patch_datetime_type():
    pw.MySQLDatabase.field_types.update({'DATETIME': 'DATETIME(6)'})
    pw.PostgresqlDatabase.field_types.update({'DATETIME': 'TIMESTAMPTZ'})


patch_datetime_type()


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
        if isinstance(value, pendulum.DateTime):
            value = datetime.datetime.fromtimestamp(
                value.timestamp(), tz=value.timezone)
        return value.astimezone(datetime.timezone.utc)


class JSONCharField(pw.CharField):
    def __init__(self, ensure_ascii=True, *args, **kwargs):
        self.ensure_ascii = ensure_ascii
        super(JSONCharField, self).__init__(*args, **kwargs)

    def db_value(self, value):
        if value is None:
            return value
        data = json.dumps(value, ensure_ascii=self.ensure_ascii)
        if len(data) > self.max_length:
            raise ValueError('Data too long for field {}.'.format(self.name))
        return data

    def python_value(self, value):
        if value is None:
            return value
        return json.loads(value)
