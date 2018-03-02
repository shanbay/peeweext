from flask import Flask
from peeweext import Peeweext

PW_DB_URL = 'sqlite+smart:///:memory:'
PW_CONN_PARAMS = {'max_connections': 2}
SECRET_KEY = 'ssshhhh'

app = Flask(__name__)
app.config.from_object(__name__)

pw = Peeweext()

pw.init_app(app)
