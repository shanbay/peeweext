from enum import Enum
from opentelemetry import trace

mysql_connector = None


class MySQLConnector(Enum):
    mysqldb = 0
    pymysql = 1


try:
    import MySQLdb
    from opentelemetry.instrumentation.mysqlclient import MySQLClientInstrumentor

    mysql_connector = MySQLConnector.mysqldb
except ImportError:
    try:
        import pymysql
        from opentelemetry.instrumentation.pymysql import PyMySQLInstrumentor

        mysql_connector = MySQLConnector.pymysql
    except ImportError:
        pass


def sync_once(func):
    def wrapper(*args, **kwargs):
        if not wrapper._done:
            wrapper._done = True
            return func(*args, **kwargs)

    wrapper._done = False
    return wrapper


@sync_once
def otel_instrument(app=None):
    if app is not None and not app.config.get_namespace("OTEL_").get("enable", False):
        return

    tp = trace.get_tracer_provider()
    if mysql_connector == MySQLConnector.mysqldb:
        MySQLClientInstrumentor().instrument(tracer_provider=tp)
    elif mysql_connector == MySQLConnector.pymysql:
        PyMySQLInstrumentor().instrument(tracer_provider=tp)
