"""Validator for peewee Model"""
import re
import functools
import ipaddress
from urllib.parse import urlsplit, urlunsplit


class ValidationError(Exception):
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


class URLValidator(RegexValidator):
    """
    See https://docs.djangoproject.com/zh-hans/2.0/ref/validators/#urlvalidator
    """

    ul = '\u00a1-\uffff'  # unicode letters range (must not be a raw string)

    # IP patterns
    ipv4_re = (
        r'(?:25[0-5]|2[0-4]\d|[0-1]?\d?\d)(?:\.'  # noqa: W605
        '(?:25[0-5]|2[0-4]\d|[0-1]?\d?\d)){3}'  # noqa: W605
    )
    ipv6_re = r'\[[0-9a-f:\.]+\]'  # (simple regex, validated later)

    # Host patterns
    hostname_re = r'[a-z' + ul + \
        r'0-9](?:[a-z' + ul + r'0-9-]{0,61}[a-z' + ul + r'0-9])?'
    # Max length for domain name labels is 63 characters per RFC 1034 sec. 3.1
    domain_re = r'(?:\.(?!-)[a-z' + ul + r'0-9-]{1,63}(?<!-))*'
    tld_re = (
        r'\.'  # dot
        r'(?!-)'  # can't start with a dash
        r'(?:[a-z' + ul + '-]{2,63}'  # domain label
        r'|xn--[a-z0-9]{1,59})'  # or punycode label
        r'(?<!-)'  # can't end with a dash
        r'\.?'  # may have a trailing dot
    )
    host_re = '(' + hostname_re + domain_re + tld_re + '|localhost)'

    _compiled_regex = re.compile(
        r'^(?:[a-z0-9\.\-\+]*)://'  # scheme is validated separately
        r'(?:\S+(?::\S*)?@)?'  # user:pass authentication
        r'(?:' + ipv4_re + '|' + ipv6_re + '|' + host_re + ')'
        r'(?::\d{2,5})?'  # port
        r'(?:[/?#][^\s]*)?'  # resource path
        r'\Z', re.IGNORECASE)
    _regex = _compiled_regex.pattern
    message = 'Enter a valid URL.'
    schemes = ['http', 'https', 'ftp', 'ftps']

    def __init__(self, schemes=None, null=False):
        self.null = null
        if schemes is not None:
            self.schemes = schemes

    def validate(self, value):
        if self.null and not value:
            return
        # Check first if the scheme is valid
        scheme = value.split('://')[0].lower()
        if scheme not in self.schemes:
            raise ValidationError(self.message)

        # Then check full URL
        try:
            super().validate(value)
        except ValidationError as e:
            # Trivial case failed. Try for possible IDN domain
            if value:
                try:
                    scheme, netloc, path, query, fragment = urlsplit(value)
                except ValueError:  # for example, "Invalid IPv6 URL"
                    raise ValidationError(self.message)
                try:
                    netloc = netloc.encode('idna').decode(
                        'ascii')  # IDN -> ACE
                except UnicodeError:  # invalid domain part
                    raise e
                url = urlunsplit((scheme, netloc, path, query, fragment))
                super().validate(url)
            else:
                raise
        else:
            # Now verify IPv6 in the netloc part
            host_match = re.search(
                r'^\[(.+)\](?::\d{2,5})?$', urlsplit(value).netloc)
            if host_match:
                potential_ip = host_match.groups()[0]
                try:
                    ipaddress.IPv6Address(potential_ip)
                except ValueError:
                    raise ValidationError(self.message)

        # The maximum length of a full host name is 253 characters per RFC 1034
        # section 3.1. It's defined to be 255 bytes or less, but this includes
        # one byte for the length of the name and one byte for the trailing dot
        # that's used to indicate absolute names in DNS.
        if len(urlsplit(value).netloc) > 253:
            raise ValidationError(self.message)


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
