import pytest
from peewee import *

from peeweext.sequence import SequenceMixin
from peeweext.fields import JsonField
from tests.flaskapp import pwdb, normal_db

db = pwdb.database


class Category(pwdb.Model):
    id = AutoField()
    content = JsonField(default={})


@pytest.fixture
def table():
    Category.create_table()
    yield
    Category.drop_table()


def test_json_field(table):
    # Create with default value
    default_category = Category.create()
    assert default_category.content == {}

    # Create with explicit value
    category = Category.create(content=['one', 'two'])
    assert category.content == ['one', 'two']

    # Update by save
    category.content = [1, 2]
    category.save()
    category = Category.get_by_id(category.id)
    assert category.content == [1, 2]

    # Update by update
    Category.update(content={'data': None}).where(
        Category.id == category.id).execute()
    category = Category.get_by_id(category.id)
    assert category.content == {'data': None}

    # Query
    query_category = Category.get(content={'data': None})
    assert query_category.content == {'data': None}
    assert query_category.id == category.id
