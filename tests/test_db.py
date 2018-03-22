import pytest
import peewee
import peeweext
import pendulum
import datetime
from io import StringIO
from peeweext import JSONCharField

from peeweext.validator import *

from tests.flaskapp import pwdb, pwmysql, pwpgsql

db = pwdb.database


class Note(pwdb.Model):
    message = peewee.TextField()
    published_at = peeweext.DatetimeTZField(null=True)

    def validate_message(self, value):
        if value == 'raise error':
            raise ValidateError


class MyNote(pwmysql.Model):
    message = peewee.TextField()
    published_at = peeweext.DatetimeTZField(null=True)

    @validates(ExclusionValidator('raise error'))
    def validate_message(self, value):
        pass


class PgNote(pwpgsql.Model):
    message = peewee.TextField()
    published_at = peeweext.DatetimeTZField(null=True)

    @validates(ExclusionValidator('raise'), LengthValidator(min_length=3, max_length=6))
    def validate_message(self, value):
        if value != 'hello':
            raise ValidateError

    def validate_nothing(self, value):
        pass


class Category(pwdb.Model):
    id = peewee.AutoField()
    content = JSONCharField(default={})


class MyCategory(pwmysql.Model):
    id = peewee.AutoField()
    content = JSONCharField(default={})


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

    with pytest.raises(peewee.IntegrityError):
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
    assert isinstance(note.validate_message, BaseValidator)

    note.message = 'raise error'
    with pytest.raises(ValidateError):
        note.validate()

    with pytest.raises(ValidateError):
        note.save()

    note.message = 'message'
    note.validate()
    note.save()
    assert note.message == Note.get_by_id(note.id).message
    # with validates decorator
    note = MyNote()
    assert isinstance(note.validate_message, list)
    assert len(note.validate_message) == 2
    assert isinstance(note.validate_message[0], BaseValidator)

    note.message = 'raise error'
    with pytest.raises(ValidateError):
        note.validate()
    # with combination
    note = PgNote()
    assert len(note.validate_message) == 3
    assert note.validate_nothing(1) is None
    note.message = 'raise'
    with pytest.raises(ValidateError):
        note.validate()
    note.message = 'no'
    with pytest.raises(ValidateError):
        note.validate()
    note.message = 'Hello'
    with pytest.raises(ValidateError):
        note.validate()
    note.message = 'hello'
    note.validate()


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


def json_field_test(CategoryModel):
    # Create with default value
    default_category = CategoryModel.create()
    assert default_category.content == {}

    # Create with explicit value
    category = CategoryModel.create(content=['one', 'two'])
    assert category.content == ['one', 'two']

    # Update by save
    category.content = [1, 2]
    category.save()
    category = CategoryModel.get_by_id(category.id)
    assert category.content == [1, 2]

    # Update by update
    CategoryModel.update(content={'data': None}).where(
        CategoryModel.id == category.id).execute()
    category = CategoryModel.get_by_id(category.id)
    assert category.content == {'data': None}

    # Query
    query_category = CategoryModel.get(content={'data': None})
    assert query_category.content == {'data': None}
    assert query_category.id == category.id


@pytest.fixture
def json_field_models():
    Category.create_table()
    MyCategory.create_table()
    yield
    Category.drop_table()
    MyCategory.drop_table()


def test_json_field_sqlite(json_field_models):
    json_field_test(Category)


def test_json_field_mysql(json_field_models):
    json_field_test(MyCategory)
