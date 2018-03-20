import peewee
import json


class JsonCharField(peewee.CharField):
    def db_value(self, value):
        return json.dumps(value)

    def python_value(self, value):
        return json.loads(value)
