import peewee
from unittest import mock, TestCase

from tests.flaskapp import pwdb
from peeweext.validators import PresenceValidator, InclusionValidator, \
    ExclusionValidator, PatternValidator, NumericalityValidator, \
    LengthValidator, RangeValidator, ValidationError

db = pwdb.database

class User(pwdb.Model):
    name = peewee.CharField(unique=True)
    email = peewee.CharField(unique=True)
    email = peewee.BooleanField(default=True)

    class Meta:
        database = db

    def validate(self, data):
        if '@' not in data['email']:
            raise ValidationError
        return data

    def validate_name(self, value):
        if value == 'invalid':
            raise ValidationError
        return value + '-cleaned'


class ModelValidateTestCase(TestCase):

    def setUp(self):
        User.create_table()

    def tearDown(self):
        User.drop_table()

    def test_valid(self):
        t = User(name='john', email='admin@example.com')
        self.assertTrue(t.is_valid())
        self.assertEqual(t.name, 'john')
        self.assertEqual(t.cleaned_data['name'], 'john-cleaned')
        t.save()
        self.assertEqual(User.get(User.id == t.id).name, 'john-cleaned')


    def test_validate_raise(self):
        t = User(name='john', email='xxx')
        with self.assertRaises(ValidationError):
            t.validate({'email': 'xxx'})
        with self.assertRaises(ValidationError):
            t.validate_name('invalid')
        with self.assertRaises(ValidationError):
            t.save()
        self.assertIsNotNone(t.errors)


class ValidatorTestCase(TestCase):

    def setUp(self):
        User.create_table()
        self.user = User(name='john', email='test@163.com')

    def tearDown(self):
        User.drop_table()

    def test_LengthValidator(self):
        with self.assertRaises(ValidationError):
            validator = LengthValidator({'minimum': 10})
            validator(self.user, '123')

        with self.assertRaises(ValidationError):
            validator = LengthValidator({'maximum': 10})
            validator(self.user, '12345678901')

        validator = LengthValidator({'minimum': 1, 'maximum': 3})
        validator(self.user, '12')

        validator = LengthValidator({'in': (1, 3)})
        validator(self.user, '12')

        with self.assertRaises(ValidationError):
            validator = LengthValidator({'in': (1, 3)})
            validator(self.user, '123')

        validator = LengthValidator({'equal': 2})
        validator(self.user, '12')

    def test_PresenceValidator(self):
        with self.assertRaises(ValidationError):
            validator = PresenceValidator(True)
            validator(self.user, '')
        with self.assertRaises(ValidationError):
            validator = PresenceValidator(True)
            validator(self.user, ' ')
        with self.assertRaises(ValidationError):
            validator = PresenceValidator(True)
            validator(self.user, None)
        validator = PresenceValidator(True)
        validator(self.user, '234')

    def test_InclusionValidator(self):
        with self.assertRaises(ValidationError):
            validator = InclusionValidator([1, 2])
            validator(self.user, 3)
        validator = InclusionValidator([1, 2, 3])
        validator(self.user, 3)

    def test_ExclusionValidator(self):
        validator = ExclusionValidator([1, 2])
        validator(self.user, 3)
        with self.assertRaises(ValidationError):
            validator = ExclusionValidator([1, 2, 3])
            validator(self.user, 3)

    def test_PatternValidator(self):
        validator = PatternValidator(r'[+-]?\d+')
        with self.assertRaises(ValidationError):
            validator(self.user, '--123')
        validator(self.user, '-123')

    def test_NumericalityValidator(self):
        with self.assertRaises(ValidationError):
            validator = NumericalityValidator(True)
            validator(self.user, 'a123')
        validator(self.user, '123')

        validator = RangeValidator({'odd': True})
        validator(self.user, 1)

    def test_RangeValidator(self):
        with self.assertRaises(ValidationError):
            validator = RangeValidator({'gt': 2})
            validator(self.user, 1)
        validator = RangeValidator({'gt': 0})
        validator(self.user, 1)
        with self.assertRaises(ValidationError):
            validator = RangeValidator({'ge': 2})
            validator(self.user, 1)
        validator = RangeValidator({'ge': 2})
        validator(self.user, 2)

        with self.assertRaises(ValidationError):
            validator = RangeValidator({'lt': 2})
            validator(self.user, 2)
        validator = RangeValidator({'lt': 10})
        validator(self.user, 1)
        with self.assertRaises(ValidationError):
            validator = RangeValidator({'le': 2})
            validator(self.user, 4)
        validator = RangeValidator({'le': 2})
        validator(self.user, 2)

        validator = RangeValidator({'eq': 1})
        validator(self.user, 1)
