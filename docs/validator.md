# Validator
    针对peeweext.Model的字段验证器

## 使用方式

```
class Note(Model):
    message = peewee.TextField()
    name = peewee.TextField()

    def validate_notafield(self, value):  # 不起作用
        raise ValidateError

    def validate_message(self, value):
        if value == 'raise error':
            raise ValidateError

    @validates(ExclusionValidator('error name'), LengthValidator(1, 20))
    def validate_name(self, value):
        pass
```

## 声明方式

### 验证方法

声明一个方法，针对单个字段进行认证，函数签名如下:

```
def validate_name(self, value):
    """
    支持的验证方法命名格式为"validate_{field_name}", 若字段名不存在，则无效。
    
    :params value: 需验证的字段值
    :return None
    :raise ValidateError 如过验证不通过，抛出异常。
    """
    if value != 'right':
        raise ValidateError('The value is not right')
```

### 组合验证器

验证方法也支持组合一些内置或者自定义的验证器来提供验证功能，格式如下：

```
@validates(ExclusionValidator('raise'), RegexValidator('[a-z]+'))
def validate_name(self, value):
    """
    可以通过validates装饰器来为验证方法添加额外验证功能。
    这个例子中验证顺序为 ExclusionValidator -> RegexValidator -> validate_name
    """
    if value != 'right':
        raise ValidateError('The value is not right')
```

## 内置认证器

目前内置认证器有ExclusionValidator InclusionValidator RegexValidator
LengthValidator, 实现的比较简单，见peeweext/validator.py

## 自定义认证器

自定义验证器需继承BaseValidator或其他Validator并实现validate方法，eg：

```
class CustomValidator(BaseValidator):
    def __init__(self, custom_arg, custom_kwarg='raise'):
        """参数个数和类型按需声明"""
        self.arg = custom_arg
        self.kwarg = custom_kwarg
        
    def validate(self, value):
        """
        :params value: 需验证的字段值
        :return None
        :raise ValidateError 如过验证不通过，抛出异常。
        """
        if value == self.arg or value == self.kwarg:
            raise ValidateError
```
