# Validator
    针对peewee.Model的字段验证器，拥有基本字段认证和自定认证功能。

## 使用方式

### 基本认证：

```
class Test(Model):
    integer = IntegerField()
    integer_with_null = IntegerField(null=True)
    integer_with_choices = IntegerField(choices=[1, 2, 3])

test = Test()
test.validate()  # raise ValidatorError
test.integer = 's'
test.integer_with_choices = 4
test.validate()
# raise
# peeweext.validator.ValidateError: {'integer': "invalid literal for int() with base 10: 's'", 'integer_with_choices': 'integer_with_choices`s value 123 not in choices: [1, 2, 3]'}
```

### 自定义认证方法：

```
class Note(Model):
    message = peewee.TextField()
    name = peewee.TextField()

    def validate_notafield(self, value):  # not work because no field named "notafield"
        raise ValidateError

    def validate_message(self, value):
        if value == 'raise error':
            raise ValidateError

    @validates(ExclusionValidator('error name'), LengthValidator(1, 20))
    def validate_name(self, value):
        pass

note = Note()
print(type(note.validate_message)  # FunctionValidator
print(type(note.validate_name))  # list of FunctionValidator
...
```

### 自定义认证器

...
