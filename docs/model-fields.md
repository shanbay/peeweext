# 扩展的Model&Field

## Field

**`DatetimeTZField`**

相对于自带的 `Datetime` Field，`DatetimeTZField` 有如下特点：

- 精度为 'micro second'
- 时间包含时区，即：
    - 返回的是 pendulum.Pendulum，自带时区
    - 赋值的 datetime 对象必须包含时区信息

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

用于提供手动排序的功能

使用时确保你的基类继承自 `peeweext.Model` 和 `peeweext.sequence.SequenceMixin`, 同时提供所需的两个字段

当需要指定排序的范围时请指定字段**属性**的名称, 举个例子:

```python
class Course(pwdb.Model, SequenceMixin):
    __seq_scope_field_name__ = 'category'

    id = AutoField()
    sequence = DoubleField()
    category = ForeignKeyField(Category, backref='courses')
    title = CharField(max_length=45, unique=True)
```

当创建一个新的对象前, 会通过信号设置一个 sequence, 当需要修改对象的 sequence 时, 请调用 `change_sequence` 方法, 任何时候都不要手动的修改 sequence 的值
