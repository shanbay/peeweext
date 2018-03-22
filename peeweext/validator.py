"""Validator for peewee Model"""


class ValidateError(BaseException):
    pass


class BaseValidator:
    def validate(self, value):
        """Validate value.
        :param value: value to validate
        :return None
        :raise ValidateError
        """
        pass

    def __call__(self, value):
        self.validate(value)


class ExclusionValidator(BaseValidator):
    def __init__(self, *args):
        self._data = args

    def validate(self, value):
        if value in self._data:
            raise ValidateError('value {:s} is in {:s}'.format(
                str(value), str(self._data)))


class InclusionValidator(ExclusionValidator):
    def validate(self, value):
        if value not in self._data:
            raise ValidateError('value {:s} is not in {:s}'.format(
                str(value), str(self._data)))


class LengthValidator(BaseValidator):
    def __init__(self, min_length, max_length):
        self.min_length = min_length
        self.max_length = max_length

    def validate(self, value):
        length = len(value)
        if self.min_length <= length <= self.max_length:
            pass
        else:
            raise ValidateError('length {:d} not in range ({:d},{:d})'.format(
                length, self.min_length, self.max_length))


class validates:
    """A decorator to store validators.

    :param args: Validator objects
    """
    def __init__(self, *args):
        self.validators = list(args)

    def __call__(self, func):
        def wrapper(instance, value):
            for validator in self.validators:
                validator(value)
            return func(instance, value)

        return wrapper
