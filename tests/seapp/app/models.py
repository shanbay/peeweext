import peewee
from peeweext import fields

from app.extensions import pwx


class Note(pwx.Model):
    message = peewee.TextField()
    published_at = fields.DatetimeTZField(null=True)
