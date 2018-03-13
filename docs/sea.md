# 与 Sea 的集成

## 添加 Config

`config/default.py`

```python
PW_DB_URL = 'sqlite+smart:///:memory:'
PW_CONN_PARAMS = {'max_connections': 2}
```

## 创建 Extension

`app/extension.py`

```python
from peeweext import Peeweext

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
