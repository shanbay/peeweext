# Validator
    针对peewee.Model的字段验证器

## 使用方式

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
