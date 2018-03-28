# 与 Flask 的集成

## 创建一个 flask app

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

## 创建一个简单的 Model

```python
import peewee

class Note(pwdb.Model):
    content = peewee.TextField()
```

## 使用 Model

```python
note = Note.create(message='Hello World')
```
