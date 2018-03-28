from sea.servicer import ServicerMeta

from app.models import Note
from app.extensions import pwx


class HelloServicer(metaclass=ServicerMeta):

    def return_normal(self, request, context):
        return not pwx.database.is_closed()
