import pytest
import peewee as pw

from peeweext.validator import *


class Test(pw.Model):
    integer = pw.IntegerField()
    integer_with_null = pw.IntegerField(null=True)
    integer_with_choices = pw.IntegerField(choices=[1, 2, 3])


def test_validator_map():
    assert validator_map[pw.IntegerField] is IntegerValidator


def test_integer():
    validator = IntegerValidator()
    validator.validate('1')
    validator(1)

    with pytest.raises(ValidateError):
        validator.validate('sfs')

    SmallIntegerValidator().validate(pow(2, 7) - 1)

    with pytest.raises(ValidateError):
        assert BigIntegerValidator().validate(pow(2, 64))


def test_string():
    validator = StringValidator()
    validator.validate(123)
    validator.validate('123')
    validator.validate(b'123')

    validator.max_length = 3
    validator.validate('123')
    with pytest.raises(ValidateError):
        validator.validate('1234')


def test_exclusion():
    validator = ExclusionValidator(1, 2, 3)
    validator(4)
    with pytest.raises(ValidateError):
        validator(1)


def test_length():
    validator = LengthValidator(1, 3)
    validator('123')
    with pytest.raises(ValidateError):
        validator('1234')


def test_model_validator():
    model = Test()
    validator = ModelValidator(Test)

    with pytest.raises(ValidateError):
        validator.validate(model)

    # null
    model.integer = 1
    model.integer_with_choices = 1
    validator.validate(model)

    model.integer_with_null = 1
    validator.validate(model)

    # choices
    model = Test()
    model.integer = 1
    model.integer_with_choices = 4
    with pytest.raises(ValidateError):
        validator.validate(model)

    model.integer_with_choices = 2
    validator.validate(model)
