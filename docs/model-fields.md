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

如果写入时，JSON 序列化后的字符串长度超过该字段的 `max_length` 定义，则会抛出 `ValueError` 异常。

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

```python
def change_sequence(self, new_sequence):
        """
        :param new_sequence: 要排到第几个

        基本的排序思路是，找到要插入位置的前一个和后一个对象，把要
        拖动对象的sequence值设置成介于两个对象之间

        注意 current_sequence，new_sequence 两个变量是数组中
        的 index，与对象的 sequence 值不要混淆
        """
```

例如 `obj.change_sequence(3)` 就是把该对象位置排到第三, 我们并不需要关心该对象当前排到哪个位置, 只需要提供新的位置即可, 需要注意`new_sequence`不能超出真实数据的范围
