# 与 Flask 的集成

## 快速入门

#### 创建一个 flask app

```python
from flask import Flask
from peeweext.flask import Peeweext

SECRET_KEY = 'ssshhhh'
PW_DB_URL = 'postgresql+pool://postgres:@127.0.0.1/peeweext'
PW_CONN_PARAMS = {'max_connections': 2}

app = Flask(__name__)
app.config.from_object(__name__)

pwdb = Peeweext()
pwdb.init_app(app)
```

#### 创建一个简单的 Model

```python
import peewee

class Note(pwdb.Model):
    content = peewee.TextField()
```

#### 使用 Model

```python
note = Note.create(message='Hello World')
```

## 相关配置

`PW_DB_URL`

> Peewee 的 [Database URL](https://peewee.readthedocs.io/en/latest/peewee/playhouse.html#db-url)

`PW_CONN_PARAMS`

> 传递给 Database 类的额外参数，类型为 `dict`。会覆盖 db_url 上的参数。例如 `PW_CONN_PARAMS={'max_connections': 20}`

`PW_MODEL`

> 基础的 Model 的绝对路径，默认为 `peeweext.model.Model`

**注意：`PW_` 为默认的配置前缀，可以在初始化 Peeweext 对象时通过指定 `ns` 参数改变。例如：**

```python
pwx1 = peeweext.sea.Peeweext(ns='PW1_')
```

会读取： `PW1_DB_URL`, `PW1_MODEL` 等配置。
