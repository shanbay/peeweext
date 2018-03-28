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

    stub = Stub(servicerclass())
    assert stub.return_normal(None)
    assert pwx.database.is_closed()

    Note.drop_table()
