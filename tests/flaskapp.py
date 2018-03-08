from flask import Flask
from peeweext import Peeweext

SECRET_KEY = 'ssshhhh'
PW_SQLITE_DB_URL = 'sqlite+smart:///:memory:'
PW_SQLITE_CONN_PARAMS = {'max_connections': 2}
PW_MYSQL_DB_URL = 'mysql+smart://root:@127.0.0.1/peeweext?max_connections=2'
PW_PGSQL_DB_URL = 'postgresql+smart://postgres:@127.0.0.1/peeweext'

app = Flask(__name__)
app.config.from_object(__name__)

pwdb = Peeweext(ns='PW_SQLITE_')
pwdb.init_app(app)

pwmysql = Peeweext(ns='PW_MYSQL_')
pwpgsql = Peeweext(ns='PW_PGSQL_')
pwmysql.init_app(app)
pwpgsql.init_app(app)
