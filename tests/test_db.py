import pytest
import peewee

from tests.flaskapp import pw


class Note(pw.Model):
    message = peewee.TextField()


@pytest.fixture
def table():
    Note.create_table()
    yield
    Note.drop_table()


def test_db(table):

    n1 = Note.create(message='Hello')
    assert pw.is_closed()
    assert Note.get_by_id(n1.id).message == 'Hello'

    n2 = Note(message='World')
    n2.save()
    assert pw.is_closed()
    assert Note.get(Note.id == n2.id).message == 'World'

    with pw.connection_context():
        with pw.atomic():
            n3 = Note.create(message='!!')
            Note.create(message='ahh')
    assert pw.is_closed()
    assert Note[n3.id].message == '!!'
