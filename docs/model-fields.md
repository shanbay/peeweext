# 扩展的Model&Field

## Field

### `peeweext.fields.DatetimeTZField`

相对于自带的 `Datetime` Field，`DatetimeTZField` 有如下特点：

- 精度为 'micro second'
- 时间包含时区，即：
    - 返回的是 pendulum.Pendulum，自带时区
    - 赋值的 datetime 对象必须包含时区信息

### `peeweext.fields.JSONCharField`

基于 `peewee.CharField` 实现的 JSONField, 可用于存储可被 JSON 化的对象，如字符串，字典等。
在写入数据库时，该字段的值会被 JSON 编码成字符串；在读取数据时，数据库中的字符串值也会被 JSON 解码成 Python 的数据结构。

如果写入时，JSON 序列化后的字符串长度超过该字段的 `max_length` 定义，则会抛出 `ValueError` 异常。


## Model

### `peeweext.model.Model`

**1. 预设 `created_at`, `updated_at`**

**2. 支持信号(`blinker.Signal`)**

**3. 支持 validation(见文档[validation](validation))**

内建的信号包括：

- `pre_save(sender, instance, created)`
- `post_save(sender, instance, created)`
- `pre_delete(sender, instance)`
- `post_delete(sender, instance)`
- `pre_init(sender, instance)`

可以定义处理函数，例如：

```python
from peeweext import pre_save

def handler(sender, instance, created):
    pass

pre_save.connect(handler)

# 或者只监听感兴趣的Model的信号:

pre_save.connect(handler, sender=Note)
```

**4. 支持 mass assignment 保护**

如果定义了类级别变量：`__attr_whitelist__`, `__attr_accessible__` 和 `__attr_protected__`

那么在通过 `Model.create` 或 `instance.update_with` 来进行批量字段赋值(mass assignment)时，只有特定的字段会赋值成功。

例如：

```python
class Model(pwdb.Model):
    __attr_whitelist__ = True
    __attr_accessible__ = {'f1', 'f2', 'f3'}
    __attr_protected__ = {'f3', 'f4'}

    f1 = peewee.IntegerField(default=0)
    f2 = peewee.IntegerField(default=0)
    f3 = peewee.IntegerField(default=0)
    f4 = peewee.IntegerField(default=0)

m1 = Model.create(f1=1, f2=2, f3=3, f4=4) # m1: {f1: 1, f2: 2, f3: 0, f4:} 只有 f1, f2 赋值成功
m1.update_with(f1=10, f2=10, f3=10, f4=10) # m1: {f1: 10, f2: 10, f3: 0, f4:} 只有 f1, f2 赋值成功

m1.f3 = 10 # m1 {f3: 10} f3 赋值成功
```

`__attr_whitelist__`, `__attr_accessible__` 和 `__attr_protected__` 具体的关系：

>  当 __attr_whitelist__ 为 True 的时候：
>     只有在 __attr_accessible__ 中 并且(AND) 不在 __attr_protected__ 中的字段能够批量赋值
>  否则:
>     只有不在 __attr_protected__ 中 或者(OR) 在 __attr_accessible__ 中的字段能够批量赋值
