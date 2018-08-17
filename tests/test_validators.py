import os

import pytest
from peeweext import validation


def test_base():
    validator = validation.BaseValidator()
    assert validator.validate(None) is None


def test_exclusion():
    validator = validation.ExclusionValidator(1, 2, 3)
    validator(4)
    with pytest.raises(validation.ValidationError):
        validator(1)


def test_inclusion():
    validator = validation.InclusionValidator(1, 2, 3)
    validator(1)
    with pytest.raises(validation.ValidationError):
        validator(4)


def test_length():
    validator = validation.LengthValidator(1, 3)
    validator('123')
    with pytest.raises(validation.ValidationError):
        validator('1234')


def test_regex():
    validator = validation.RegexValidator('[a-z]+')
    validator.validate('xyz')
    with pytest.raises(validation.ValidationError):
        validator('Xyz')


def create_path(filename):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), filename))


def test_url_validator():
    validator = validation.URLValidator(null=True)
    with open(create_path('valid_urls.txt'), encoding='utf8') as f:
        for url in f:
            assert validator.validate(url.strip()) is None

    assert validator.validate('') is None

    with open(create_path('invalid_urls.txt'), encoding='utf8') as f:
        for url in f:
            with pytest.raises(validation.ValidationError):
                validator.validate(url.strip())
