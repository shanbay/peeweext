import pytest
import peewee
import peeweext
import pendulum
import datetime
from io import StringIO

from tests.flaskapp import pwdb, pwmysql, pwpgsql

db = pwdb.database


class Note(pwdb.Model):
    message = peewee.TextField()
    published_at = peeweext.DatetimeTZField(null=True)


class MyNote(pwmysql.Model):
    message = peewee.TextField()
    published_at = peeweext.DatetimeTZField(null=True)


class PgNote(pwpgsql.Model):
    message = peewee.TextField()
    published_at = peeweext.DatetimeTZField(null=True)


@pytest.fixture
def table():
    Note.create_table()
    yield
    Note.drop_table()


def test_db(table):

    n1 = Note.create(message='Hello')
    assert db.is_closed()
    assert Note.get_by_id(n1.id).message == 'Hello'

    n2 = Note(message='World')
    n2.save()
    assert db.is_closed()
    assert Note.get(Note.id == n2.id).message == 'World'

    with db.connection_context():
        with db.atomic():
            n3 = Note.create(message='!!')
            Note.create(message='ahh')
    assert db.is_closed()
    assert Note[n3.id].message == '!!'


def test_model(table):
    n = Note.create(message='Hello')
    updated_at = n.updated_at

    with pytest.raises(ValueError):
        n.created_at = None
        n.save()

    n = Note.get(id=n.id)

    with pytest.raises(ValueError):
        n.published_at = '1900-01-01T00:00:00'
        n.save()

    with pytest.raises(ValueError):
        n.published_at = datetime.datetime.utcnow()
        n.save()

    n.published_at = pendulum.now()
    n.save()
    assert n.updated_at > updated_at

    out = StringIO()

    def post_delete(sender, instance):
        out.write('post_delete received')

    peeweext.post_delete.connect(post_delete, sender=Note)
    n.delete_instance()

    assert 'post_delete' in out.getvalue()


def test_validator(table):
    note = Note()
    assert not note.is_validated
    assert len(note.errors) > 0
    with pytest.raises(ValueError):
        note.save()

    note.message = 'message'
    assert note.is_validated
    note.save()
    assert note.message == Note.get_by_id(note.id).message


def test_mysql():
    MyNote.create_table()
    dt = datetime.datetime.now(
            tz=datetime.timezone(datetime.timedelta(hours=8)))
    n = MyNote(message='hello', published_at=dt)
    n.save()
    n = MyNote.get_by_id(n.id)
    assert n.published_at.timestamp() == dt.timestamp()
    MyNote.drop_table()


def test_pgsql():
    PgNote.create_table()
    dt = datetime.datetime.now(
            tz=datetime.timezone(datetime.timedelta(hours=8)))
    n = PgNote(message='hello', published_at=dt)
    n.save()
    n = PgNote.get_by_id(n.id)
    assert n.published_at.timestamp() == dt.timestamp()
    PgNote.drop_table()
