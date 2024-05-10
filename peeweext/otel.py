from opentelemetry import trace
from opentelemetry.instrumentation.mysqlclient import MySQLClientInstrumentor


def sync_once(func):
    def wrapper(*args, **kwargs):
        if not wrapper._done:
            wrapper._done = True
            return func(*args, **kwargs)

    wrapper._done = False
    return wrapper


@sync_once
def otel_instrument(app=None):
    if app is None or app.config.get_namespace("OTEL_").get("enable", False):
        MySQLClientInstrumentor().instrument(
            tracer_provider=trace.get_tracer_provider()
        )
