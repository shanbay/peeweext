# 与 Sea 的集成

## 添加 Config

`config/default.py`

```python
PW_DB_URL = 'mysql+pool://root:@127.0.0.1/peeweext?max_connections=2'
MIDDLEWARES = [
    'sea.middleware.ServiceLogMiddleware',
    'sea.middleware.RpcErrorMiddleware',
    'peeweext.sea.PeeweextMiddleware' # It's very important!!!!
]
```

## 创建 Extension

`app/extension.py`

```python
from peeweext.sea import Peeweext

pwdb = Peeweext()
```

## 创建 Model

`app/model.py`

```python
from app.extensions import pwdb

class Note(pwdb.Model):
    content = peewee.TextField()
```

## 使用 Model

```python
note = Note.create(message='Hello World')
```
