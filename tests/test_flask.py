import peewee
from flask import Flask

from .flaskapp import app, pwmysql, PW_MYSQL_DB_URL


class Comment(pwmysql.Model):
    author = peewee.TextField


@app.route("/comment")
def get_comment():
    Comment.get_or_none()
    return "ok!"


def test_flask_init_app_duplicate():
    from .flaskapp import app
    try:
        Comment.create_table()

        client = app.test_client()

        app1 = Flask("other app")
        app1.config.setdefault("PW_MYSQL_DB_URL", PW_MYSQL_DB_URL)

        # init_app to other app will update instance's database connection pool
        pwmysql.init_app(app1)

        rv = client.get("/comment")
        assert rv.status_code == 200

        # test after init_app again, connection pool synced between peeweext instance and Model
        assert pwmysql.database == Comment._meta.database

        # test before/after request works fine
        assert pwmysql.database.is_closed()
    finally:
        Comment.drop_table()
