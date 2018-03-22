import pytest

from peeweext.validator import *


def test_base():
    validator = BaseValidator()
    assert validator.validate(None) is None


def test_exclusion():
    validator = ExclusionValidator(1, 2, 3)
    validator(4)
    with pytest.raises(ValidateError):
        validator(1)


def test_inclusion():
    validator = InclusionValidator(1, 2, 3)
    validator(1)
    with pytest.raises(ValidateError):
        validator(4)


def test_length():
    validator = LengthValidator(1, 3)
    validator('123')
    with pytest.raises(ValidateError):
        validator('1234')
