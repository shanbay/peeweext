"""Validator for peewee Model"""
from collections import defaultdict

import peewee as pw


validator_map = {}  # record  relationship between field and validator eg: {IntegerField: IntegerValidator}


def register(field_cls):
    """Register Validator to validator map"""

    def wrapper(validator_cls):
        validator_map[field_cls] = validator_cls
        return validator_cls

    return wrapper


class ValidateError(BaseException):
    pass


class BaseValidator:
    """Base validator for single peewee field"""
    error_message = 'Validate error'
    validated_value = None

    def convert(self, value):
        """Convert source value to expect type.
        :return object, expect type
        :raise BaseException
        """
        return value

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
        try:
            self.validated_value = self.convert(value)
            validated = self._validate(self.validated_value, extra_value=extra_value)
        except Exception as e:
            raise ValidateError(e) from e
        # no exception but validate failed
        if not validated:
            raise ValidateError(self.error_message)

    def __call__(self, value, extra_value=None):
        self.validate(value, extra_value=extra_value)


@register(pw.IntegerField)
class IntegerValidator(BaseValidator):
    min_value = -2147483648
    max_value = 2147483647

    def convert(self, value):
        return int(value)

    def _validate(self, value, extra_value=None):
        if self.min_value <= value <= self.max_value:
            return True
        else:
            self.error_message = 'This number {:d} not in range ({:d}, {:d})'.format(
                value, self.min_value, self.max_value)
            return False


@register(pw.BigIntegerField)
class BigIntegerValidator(IntegerValidator):
    min_value = -9223372036854775808
    max_value = 9223372036854775807


@register(pw.SmallIntegerField)
class SmallIntegerValidator(IntegerValidator):
    min_value = -128
    max_value = 127


@register(pw.TextField)
class StringValidator(BaseValidator):
    max_length = -1

    def convert(self, value):
        return str(value)

    def _validate(self, value, extra_value=None):
        if self.max_length > 0:
            value_length = len(value.encode())
            if value_length <= self.max_length:
                return True
            else:
                self.error_message = 'Value`s length {:d} is big than {:d}'.format(value_length, self.max_length)
                return False
        else:
            return True


# Custom validator
class ExclusionValidator(BaseValidator):
    def __init__(self, *args):
        self._data = args

    def _validate(self, value, extra_value=None):
        for data in self._data:
            if data == value:
                self.error_message = 'value {:s} is equal to {:s}'.format(str(value), str(data))
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
            self.error_message = 'length {:d} not in range ({:d}, {:d})'.format(
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
    """A decorator to convert model validation method to a list of custom validators.

    :param args: Validator objects
    :return A function return list of validators
    """
    validators = list(args)

    def decorate(func):
        validators.append(FunctionValidator(func))
        return validators

    return decorate


class ModelValidator:
    """Validator for peewee model.

    :param model: type(peewee.Model)
    """
    def __init__(self, model):
        self.validators = defaultdict(list)  # eg: {'age': [IntegerField()]}
        self.fields = model._meta.fields

        for name, field in self.fields.items():
            field_cls = field.__class__
            if field_cls in validator_map:
                self.validators[name].append(validator_map[field.__class__]())
            elif field_cls is not pw.AutoField:
                self.validators[name].append(BaseValidator())

    def add_validator(self, field_name, validator):
        """Add validators.

        :param field_name: str
        :param validator: BaseValidator
        """
        self.validators[field_name].insert(0, validator)

    def validate(self, model):
        """
        Validate all value in model.

        :param model: peewee.Model
        :raise ValidateError
        :return: None
        """
        errors = {}

        for name, validators in self.validators.items():
            field = self.fields[name]
            value = getattr(model, name)
            # field initialization arguments
            null = getattr(field, 'null')
            choices = getattr(field, 'choices')

            if value is not None:
                # validate all validators
                try:
                    for validator in validators:
                        if isinstance(validator, FunctionValidator):
                            validator(value, extra_value=model)
                        else:
                            validator(value)
                except ValidateError as e:
                    errors[name] = str(e)
            elif not null:
                errors[name] = '{:s} have no value yet'.format(name)

            if choices and value not in choices:
                errors[name] = '{:s}`s value {:s} not in choices: {:s}'.format(name, str(value), str(choices))

        if errors:
            raise ValidateError(str(errors))
