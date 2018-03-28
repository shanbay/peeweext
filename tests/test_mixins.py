import pytest
import peewee as pw

from peeweext.mixins import SequenceMixin
from tests.flaskapp import pwdb

db = pwdb.database


class Category(pwdb.Model):
    id = pw.AutoField()
    name = pw.CharField(max_length=45, unique=True)


class Course(pwdb.Model, SequenceMixin):
    __seq_scope_field_name__ = 'category'

    id = pw.AutoField()
    sequence = pw.DoubleField(null=True)
    category = pw.ForeignKeyField(Category, backref='courses')
    title = pw.CharField(max_length=45, unique=True)


class Book(SequenceMixin, pwdb.Model):
    __seq_scope_field_name__ = None

    id = pw.AutoField()
    sequence = pw.DoubleField(null=True)


@pytest.fixture
def table():
    Category.create_table()
    Course.create_table()
    Book.create_table()
    yield
    Category.drop_table()
    Course.drop_table()
    Book.drop_table()


def test_sequence(table):
    for name in ['Python', 'Ruby']:
        Category.create(name=name)
    category_1, category_2 = Category.select()
    for title in ['Step1', 'Step2', 'Step3']:
        Course.create(title=category_1.name + title, category_id=category_1.id)
        Course.create(title=category_2.name + title, category_id=category_2.id)

    c = category_1.courses.first()
    assert c.sequence, 1

    current = 1
    for course in Course.select().order_by(Course.id)[1:]:
        assert course.sequence > current
        current = course.sequence

    c.change_sequence(new_sequence=2)
    assert c.sequence, 2
    c.change_sequence(1)
    assert c.sequence, 1

    courses = Course.select()
    pre_course = courses.first()
    for c in courses[1:]:
        assert c.category_id >= pre_course.category_id
        if c.category_id == pre_course.category_id:
            assert c.sequence > pre_course.sequence
        pre_course = c

    b = Book.create()
    assert Book.select().count() == 1
    assert b.sequence, 1
    b.change_sequence(1)
    assert b.sequence, 1
    with pytest.raises(ValueError):
        b.change_sequence(0)
    with pytest.raises(ValueError):
        b.change_sequence(2)
    Book.create()
    b.change_sequence(2)
    assert b.sequence, 2


def test_sequence_auto_loosen(table):
    category = Category.create(name='Python')
    for title in ['Step1', 'Step2', 'Step3']:
        Course.create(title=category.name + title, category_id=category.id)

    for round_ in range(50):
        c = Course.select().order_by(-Course.sequence).first()
        c.change_sequence(new_sequence=2)
        ac = Course.select().order_by(+Course.sequence)[1]
        assert ac.id == c.id
