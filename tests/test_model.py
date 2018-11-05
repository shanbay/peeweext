import pytest
import peewee
import peeweext
import pendulum
import datetime
from io import StringIO
import inspect

from peeweext.fields import JSONCharField
from peeweext import validation as val

from tests.flaskapp import pwdb, pwmysql, pwpgsql

db = pwdb.database


class Note(pwdb.Model):
    message = peewee.TextField()
    published_at = peeweext.fields.DatetimeTZField(null=True)

    def validate_message(self, value):
        if value == 'raise error':
            raise val.ValidationError


class MyNote(pwmysql.Model):
    message = peewee.TextField()
    published_at = peeweext.fields.DatetimeTZField(null=True)

    @val.validates(val.ExclusionValidator('raise error'))
    def validate_message(self, value):
        pass


class PgNote(pwpgsql.Model):
    message = peewee.TextField()
    published_at = peeweext.fields.DatetimeTZField(null=True)

    @val.validates(
        val.ExclusionValidator('raise'),
        val.LengthValidator(min_length=3, max_length=6))
    def validate_message(self, value):
        if value != 'hello':
            raise val.ValidationError

    def validate_nothing(self, value):
        return 'nothing'


class Category(pwdb.Model):
    id = peewee.AutoField()
    content = JSONCharField(max_length=128, default={})
    remark = JSONCharField(max_length=128, null=True)


class MyCategory(pwmysql.Model):
    id = peewee.AutoField()
    content = JSONCharField(max_length=128, default={})
    remark = JSONCharField(max_length=128, null=True)


class MyNotebook(pwmysql.Model):
    note = peewee.ForeignKeyField(MyNote, backref='notes', null=True)


@pytest.fixture
def table():
    Note.create_table()
    PgNote.create_table()
    MyNote.create_table()
    MyNotebook.create_table()
    yield
    MyNotebook.drop_table()
    Note.drop_table()
    PgNote.drop_table()
    MyNote.drop_table()


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

    peeweext.model.post_delete.connect(post_delete, sender=Note)
    n.delete_instance()

    assert 'post_delete' in out.getvalue()


def test_validator(table):
    note = Note()
    assert inspect.ismethod(note.validate_message)

    note.message = 'raise error'
    assert not note.is_valid
    assert len(note.errors) > 0
    with pytest.raises(val.ValidationError):
        note.save()
    note.save(skip_validation=True)

    note.message = 'message'
    note._validate()
    note.save()
    assert note.message == Note.get_by_id(note.id).message
    # with validates decorator
    note = MyNote()
    assert inspect.ismethod(note.validate_message)

    note.message = 'raise error'
    with pytest.raises(val.ValidationError):
        note.save()
    note.message = 'no error'
    note.save()
    # with combination
    note = PgNote()
    assert inspect.ismethod(note.validate_message)
    assert note.validate_nothing(None) == 'nothing'
    note.message = 'raise'
    with pytest.raises(val.ValidationError):
        note.save()
    note.message = 'no'
    with pytest.raises(val.ValidationError):
        note.save()
    note.message = 'Hello'
    with pytest.raises(val.ValidationError):
        note.save()
    note.message = 'hello'
    note.save()


def test_instance_delete(table):
    # test delete
    note = Note.create(message='Hello')
    with pytest.raises(UserWarning):
        note.delete().execute()

    Note.delete().execute()
    ins = Note.get_or_none(Note.id == note.id)
    assert ins is None

    # test delete_instance
    note = Note.create(message='Hello')
    note.delete_instance()
    ins = Note.get_or_none(Note.id == note.id)
    assert ins is None

    # test delete
    my_note = MyNote.create(message='Hello')
    with pytest.raises(UserWarning):
        my_note.delete().execute()

    MyNote.delete().execute()
    ins = MyNote.get_or_none(MyNote.id == my_note.id)
    assert ins is None

    # test delete_instance
    with pytest.raises(peewee.IntegrityError):
        my_note = MyNote.create(message='Hello')
        _ = MyNotebook.create(note=my_note)
        my_note.delete_instance()
    MyNotebook.delete().execute()
    MyNote.delete().execute()

    # test delete_instance recursive
    my_note = MyNote.create(message='Hello')
    my_notebook = MyNotebook.create(note=my_note)
    my_note.delete_instance(recursive=True, delete_nullable=True)
    ins = MyNote.get_or_none(MyNote.id == my_note.id)
    assert ins is None
    ins = MyNotebook.get_or_none(MyNotebook.id == my_notebook.id)
    assert ins is None

    my_note = MyNote.create(message='Hello')
    my_notebook = MyNotebook.create(note=my_note)
    my_note.delete_instance(recursive=True)
    ins = MyNote.get_or_none(MyNote.id == my_note.id)
    assert ins is None
    ins = MyNotebook.get_or_none(MyNotebook.id == my_notebook.id)
    assert ins is not None
    assert ins.note is None
    MyNotebook.delete().execute()

    # test delete
    pg_note = PgNote.create(message='hello')
    with pytest.raises(UserWarning):
        pg_note.delete().execute()

    PgNote.delete().execute()
    ins = PgNote.get_or_none(PgNote.id == pg_note.id)
    assert ins is None

    # test delete_instance
    pg_note = PgNote.create(message='hello')
    pg_note.delete_instance()
    ins = PgNote.get_or_none(PgNote.id == pg_note.id)
    assert ins is None


def test_datetime():
    # mysql
    MyNote.create_table()
    dt = datetime.datetime.now(
        tz=datetime.timezone(datetime.timedelta(hours=8)))
    n = MyNote(message='hello', published_at=dt)
    n.save()
    n = MyNote.get_by_id(n.id)
    assert n.published_at.timestamp() == dt.timestamp()
    MyNote.drop_table()

    # pgsql
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
    assert default_category.remark is None

    default_category.remark = None
    default_category.save()
    assert default_category.remark is None

    # Create with explicit value
    category = CategoryModel.create(content=['one', 'two'])
    assert category.content == ['one', 'two']

    # Create with long data
    with pytest.raises(ValueError) as exc:
        CategoryModel.create(content=list(range(10000)))
        assert exc.args[0] == 'Data too long for field content.'

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
