# Mixins

### `peeweext.mixins.SequenceMixin`

用于提供手动排序的功能

使用时确保你的基类继承自 `peeweext.Model` 和 `peeweext.mixins.SequenceMixin`, 同时提供所需的两个字段

当需要指定排序的范围时请指定字段**属性**的名称, 举个例子:

```python
class Course(pwdb.Model, SequenceMixin):
    __seq_scope_field_name__ = 'category'

    id = AutoField()
    sequence = DoubleField()
    category = ForeignKeyField(Category, backref='courses')
    author = pw.ForeignKeyField(Author, backref='authors')
    title = CharField(max_length=45, unique=True)
```

需要按照多个字段指定排序范围时，`__seq_scope_field_name__` 写成如下形式：

```python
__seq_scope_field_name__ = 'category,author'
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
