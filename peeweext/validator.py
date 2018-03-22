"""Validator for peewee Model"""


class ValidateError(BaseException):
    pass


class BaseValidator:
    """Base validator for single peewee field"""
    error_message = 'Validate error'
    validated_value = None

    def _validate(self, value, extra_value=None):
        """Validate value.
        Return False or raise exception when validate failed

        :param value: value to validate
        :param extra_value: extra value if needed
        :return bool
        :raise BaseException
        """
        return True

    def validate(self, value, extra_value=None):
        """Validate value.
        :param value: value to validate
        :param extra_value: extra value if needed
        :return None
        :raise ValidateError
        """
        # convert and validate
        validated = self._validate(value, extra_value=extra_value)
        # no exception but validate failed
        if not validated:
            raise ValidateError(self.error_message)

    def __call__(self, value, extra_value=None):
        self.validate(value, extra_value=extra_value)


# Custom validator
class ExclusionValidator(BaseValidator):
    def __init__(self, *args):
        self._data = args

    def _validate(self, value, extra_value=None):
        for data in self._data:
            if data == value:
                self.error_message = 'value {:s} is equal to {:s}'.format(
                    str(value), str(data))
                return False
        return True


class LengthValidator(BaseValidator):
    def __init__(self, min_length, max_length):
        self.min_length = min_length
        self.max_length = max_length

    def _validate(self, value, extra_value=None):
        length = len(value)
        if self.min_length <= length <= self.max_length:
            return True
        else:
            self.error_message = 'length {:d} not in range ({:d},{:d})'.format(
                length, self.min_length, self.max_length)
            return False


class FunctionValidator(BaseValidator):
    """Convert custom validation function to Validator object"""
    def __init__(self, func):
        self._func = func

    def _validate(self, value, extra_value=None):
        """Validate value by model`s method

        :param value:
        :param extra_value: peewee.Model instance
        :return:
        """
        self._func(extra_value, value)
        return True


def validates(*args):
    """A decorator to convert model validation method to
    a list of custom validators.

    :param args: Validator objects
    :return A function return list of validators
    """
    validators = list(args)

    def decorate(func):
        validators.append(FunctionValidator(func))
        return validators

    return decorate
