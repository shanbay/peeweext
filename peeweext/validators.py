import re
import json
import functools


class ValidationError(ValueError):
    detail = 'Invalid input.'

    def __init__(self, detail=None):
        if detail is not None:
            self.detail = detail

    def __str__(self):
        if isinstance(self.detail, str):
            return self.detail
        try:
            return json.dumps(self.detail)
        except TypeError:
            return str(self.detail)



class BaseValidator:
    """"Base Class"""
    pass


class PresenceValidator(BaseValidator):
    """validates that the specified value are not empty
    :param status: `True` or `False`
    """

    def __init__(self, status):
        self._status = status if isinstance(status, bool) else False

    def __call__(self, instance, value):
        if not self._status:
            return value

        if isinstance(value, str):
            if value.strip(' ') == '':
                raise ValidationError("can't be blank")

        if value is not None:
            return value

        raise ValidationError("can't be blank")


class InclusionValidator(BaseValidator):
    """validates that the values are included in a given set
    :param candidate: candidates, an object implements `__contains__`
    """

    def __init__(self, candidate):
        self._candidate = candidate

    def __call__(self, instance, value):
        if value not in self._candidate:
            raise ValidationError("is not included in the list")
        return value


class ExclusionValidator(BaseValidator):
    """validates that the values are not included in a given set
    :param candidate
    """

    def __init__(self, candidate):
        self._candidate = candidate

    def __call__(self, instance, value):
        if value in self._candidate:
            raise ValidationError("is reserved")
        return value


class PatternValidator(BaseValidator):
    """validates the values by testing whether they match a given regular
    expression
    :param pattern: string type regex
    """

    def __init__(self, pattern):
        self._pattern = re.compile(pattern)

    def __call__(self, instance, value):
        if not self._pattern.match(value):
            raise ValidationError("is invalid")
        return value


class NumericalityValidator(BaseValidator):
    """validates that the value have only numeric values
    """

    NUM_REGEX = re.compile(r'[+-]?\d+')

    def __init__(self, kwargs):
        self._status = False
        if isinstance(kwargs, bool):
            self._status = kwargs
        else:
            self._only_integer = kwargs.get('only_integer')
            self._odd = kwargs.get('odd')
            self._even = kwargs.get('even')

    def __call__(self, instance, value):
        if isinstance(value, str):
            if hasattr(self, '_only_integer') and self._only_integer:
                if not self.NUM_REGEX.match(value.strip()):
                    raise ValidationError("is not a number")
                value = int(value)
            else:
                try:
                    value = float(value)
                except ValueError:
                    raise ValidationError("is not a number")

        if hasattr(self, '_odd') and self._odd and value % 2 != 1:
            raise ValidationError("must be odd")

        if hasattr(self, '_even') and self._even and value % 2 != 0:
            raise ValidationError("must be even")

        return value


class RangeValidator(BaseValidator):
    """validates that the value whether in the range
    :param interval: accept key `gt` `ge` `lt` `le` `eq`
    """

    def __init__(self, interval):
        self._gt = interval.get('gt', float('-INF'))
        self._ge = interval.get('ge', float('-INF'))
        self._lt = interval.get('lt', float('INF'))
        self._le = interval.get('le', float('INF'))
        self._eq = interval.get('eq')

    def __call__(self, instance, value):
        if self._eq and self._eq != value:
            raise ValidationError("must be equal to {}".formate(self._eq))

        if not self._ge <= value:
            raise ValidationError(
                "value must be greater than or equal to {}".format(self._ge))
        if not self._le >= value:
            raise ValidationError(
                "value must be less than or equal to {}".format(self._le))

        if not self._gt < value:
            raise ValidationError(
                "value must be greater than {}".format(self._gt))
        if not self._lt > value:
            raise ValidationError(
                "value must be less than {}".format(self._lt))

        return value


class LengthValidator(BaseValidator):
    """validates that the value length
    :param len_interval: accept key `minimum` `maximum` `in` `eq`
    """

    def __init__(self, len_interval):
        self._minimum = len_interval.get('minimum', 0)
        self._maximum = len_interval.get('maximum', float('INF'))
        _in = len_interval.get('in')
        if _in is not None:
            self._minimum, self._maximum = _in
        self._equal = len_interval.get('eq')

    def __call__(self, instance, value):
        length = len(value)
        if self._equal and length != self._equal:
            raise ValidationError("length must be {}".format(self._equal))
        if not self._minimum < length:
            raise ValidationError(
                "length must be greater than {}".format(self._minimum))
        if not self._maximum > length:
            raise ValidationError(
                "length must be less than {}".format(self._maximum))
        return value



class ValidatorDispatcher:

    mapping = {
        'presence': PresenceValidator,
        'inclusion': InclusionValidator,
        'exclusion': ExclusionValidator,
        'pattern': PatternValidator,
        'length': LengthValidator,
        'numericality': NumericalityValidator,
        'range': RangeValidator
    }

    @classmethod
    def dispathcer(cls, kwargs):
        chain = []
        for validator_name, args in kwargs.items():
            validator_cls = cls.mapping.get(validator_name)
            if validator_cls is not None:
                chain.append(validator_cls(args))
        return chain


class validates:  # noqa
    """decorator
    """

    def __init__(self, **kwargs):
        self._chain = ValidatorDispatcher.dispathcer(kwargs)

    def __call__(self, func):
        for validate in self._chain:
            validate.func_name = func.__name__

        @functools.wraps(func)
        def wrapper(instance, value):
            for validate in self._chain:
                value = validate(instance, value)
            return func(instance, value)

        return wrapper
