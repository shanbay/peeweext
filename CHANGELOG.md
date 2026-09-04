# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project adheres to Semantic Versioning.

## [1.2.9] - 2026-08-14

- Fix `AttributeError: module 'peewee' has no attribute 'basestring'` raised by `Model.save(only=[...])` on peewee>=4, which dropped the py2-compat `basestring` alias.
- Fix `Model.delete_instance(recursive=True)` failing with a foreign key constraint error: nullable FK dependents were never discovered (and thus never nulled out) because `search_nullable` was incorrectly tied to `delete_nullable`.
- Fix `URLValidator` raising an uncaught `ValueError` (instead of `ValidationError`) for malformed bracketed IPv6 hosts like `[::1:2::3]` on Python 3.9+.

## [1.2.8] - 2024-05-15

- Compatible with both MySQLClient and PyMySQL

## [1.2.7] - 2024-04-28

- Add MySQLClientInstrumentor used to automatic tracing the requests from mysqlClient, the `instrument()` method should be invoked before `connect()`.

## [1.2.6] - 2021-12-29

- Update `updated_at` field implicitly when updating with the `only` option.

```
some_record.a_field = "updatede a field"
# updated fields: a_field, updated_at
some_record.save(only=["a_field"])
```

## [1.2.3] - 2021-04-21

- ensure_ascii is provided in JSONCharField to support storing Chinese in non-ascii way

## [1.1.0] - 2019-02-15

### added

- Mass assignment protection

### changed

- replace count function with fn.SQL COUNT

## [1.0.0] - 2018-11-05

### changed

- Raise UserWarning when trying to use delete() in instance.

[1.1.0]: https://github.com/shanbay/peeweext/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/shanbay/peeweext/releases/tag/v1.0.0
