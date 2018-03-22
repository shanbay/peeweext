"""Validator for peewee Model"""
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
            value_length = len(value.decode())
            if value_length < self.max_length:
                return True
            else:
                self.error_message = 'Value`s length {:d} is big than {:d}'.format(value_length, self.max_length)
                return False
        else:
            return True


class ModelValidator:
    """Validator for peewee model.

    :param model: type(peewee.Model)
    """
    def __init__(self, model):
        self.validators = {}  # eg: {'age': IntegerField()}
        self.fields = model._meta.fields

        for name, field in self.fields.items():
            field_cls = field.__class__
            if field_cls in validator_map:  # only validate field we know
                self.validators[name] = validator_map[field.__class__]()
            elif field_cls is not pw.AutoField:
                self.validators[name] = BaseValidator()

    def validate(self, model):
        """
        Validate all value in model.

        :param model: peewee.Model
        :raise ValidateError
        :return: None
        """
        errors = {}

        for name, validator in self.validators.items():
            field = self.fields[name]
            value = getattr(model, name)
            # field initialization arguments
            null = getattr(field, 'null')
            choices = getattr(field, 'choices')

            if value is not None:
                # validate by validators
                try:
                    validator.validate(value)
                    setattr(model, name, validator.validated_value)
                except ValidateError as e:
                    errors[name] = str(e)
            elif not null:
                raise ValidateError('{:s} have no value yet'.format(name))

            if choices and value not in choices:
                raise ValidateError('{:s}`s value {:s} not in choices: {:s}'.format(name, str(value), str(choices)))

        if errors:
            raise ValidateError(str(errors))
