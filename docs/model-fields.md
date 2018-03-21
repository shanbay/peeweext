# 扩展的Model&Field

## Field

### `DatetimeTZField`

相对于自带的 `Datetime` Field，`DatetimeTZField` 有如下特点：

- 精度为 'micro second'
- 时间包含时区，即：
    - 返回的是 pendulum.Pendulum，自带时区
    - 赋值的 datetime 对象必须包含时区信息

### `JSONCharField`
基于 `peewee.CharField` 实现的 JSONField, 可用于存储可被 JSON 化的对象，如字符串，字典等。  
在写入数据库时，该字段的值会被 JSON 编码成字符串；在读取数据时，数据库中的字符串值也会被 JSON 解码成 Python 的数据结构。

## Model

### `peeweext.Model`

**1. 预设 `created_at`, `updated_at`**

**2. 支持信号(`blinker.Signal`)**

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


### `peeweext.sequence.SequenceMixin`
