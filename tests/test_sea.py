import os.path
from sea import create_app
from sea.test.stub import Stub

os.environ.setdefault('SEA_ENV', 'testing')
root = os.path.join(os.path.dirname(__file__), 'seapp')
_app = create_app(root)


def test_sea():
    from app.models import Note
    Note.create_table()

    pwx = _app.extensions.pwx
    servicerclass = _app.servicers.HelloServicer[1]

    _app1 = create_app(root)

    # init_app to other app will update instance's database connection pool
    pwx.init_app(_app1)

    stub = Stub(servicerclass())
    assert stub.return_normal(None)

    # test after init_app again, connection pool synced between peeweext instance and Model
    assert pwx.database == Note._meta.database

    assert pwx.database.is_closed()

    Note.drop_table()
