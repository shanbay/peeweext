import peewee
import json


class JsonField(peewee.CharField):
    def db_value(self, value):
        return json.dumps(value)

    def python_value(self, value):
        return json.loads(value)
