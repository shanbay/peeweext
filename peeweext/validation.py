"""Validator for peewee Model"""
import re
import functools


class ValidationError(BaseException):
    pass


class BaseValidator:
    def validate(self, value):
        """Validate value.
        :param value: value to validate
        :return None
        :raise ValidationError
        """
        pass

    def __call__(self, value):
        self.validate(value)


class ExclusionValidator(BaseValidator):
    def __init__(self, *args):
        self._data = args

    def validate(self, value):
        if value in self._data:
            raise ValidationError('value {:s} is in {:s}'.format(
                str(value), str(self._data)))


class InclusionValidator(ExclusionValidator):
    def validate(self, value):
        if value not in self._data:
            raise ValidationError('value {:s} is not in {:s}'.format(
                str(value), str(self._data)))


class RegexValidator(BaseValidator):
    def __init__(self, regex):
        self._regex = regex
        self._compiled_regex = re.compile(regex)

    def validate(self, value):
        """Validate string by regex
        :param value: str
        :return:
        """
        if not self._compiled_regex.match(value):
            raise ValidationError(
                'value {:s} not match r"{:s}"'.format(value, self._regex))


class LengthValidator(BaseValidator):
    def __init__(self, min_length, max_length):
        self.min_length = min_length
        self.max_length = max_length

    def validate(self, value):
        length = len(value)
        if self.min_length <= length <= self.max_length:
            pass
        else:
            raise ValidationError(
                'length {:d} not in range ({:d},{:d})'.format(
                    length, self.min_length, self.max_length))


class validates:
    """A decorator to store validators.

    :param args: Validator objects
    """
    def __init__(self, *args):
        self.validators = list(args)

    def __call__(self, func):
        for validator in self.validators:
            validator.func_name = func.__name__

        @functools.wraps(func)
        def wrapper(instance, value):
            for validator in self.validators:
                validator(value)
            return func(instance, value)

        return wrapper
