import re

from pyramid.httpexceptions import HTTPBadRequest
from pyramid.view import view_config, view_defaults

from lms.security import Permissions
from lms.services import VitalSourceService


@view_defaults(renderer="json", permission=Permissions.API)
class VitalSourceAPIViews:
    def __init__(self, request):
        self.request = request
        self.svc = request.find_service(VitalSourceService)

    @view_config(route_name="vitalsource_api.books.info")
    def book_info(self):
        return self.svc.get_book_info(self._book_id)

    @view_config(route_name="vitalsource_api.books.toc")
    def table_of_contents(self):
        return self.svc.get_table_of_contents(self._book_id)

    _VALID_BOOK_ID = re.compile(r"^[\dA-Z-]+$")

    @property
    def _book_id(self):
        book_id = self.request.matchdict["book_id"]

        if not self._VALID_BOOK_ID.match(book_id):
            raise HTTPBadRequest("Invalid `book_id`. It must only contain [0-9A-Z-].")

        return book_id
