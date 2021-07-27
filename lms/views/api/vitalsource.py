from pyramid.httpexceptions import HTTPNotFound
from pyramid.view import view_config, view_defaults

from lms.security import Permissions
from lms.services.exceptions import ProxyAPIError


@view_defaults(renderer="json", permission=Permissions.API)
class VitalSourceAPIViews:
    def __init__(self, request):
        self.request = request
        self.vitalsource_service = request.find_service(name="vitalsource")

    @view_config(route_name="vitalsource_api.books.info")
    def book_info(self):
        book_id = self.request.matchdict["book_id"]

        book_info = self.vitalsource_service.book_info(book_id)

        if not book_info:
            raise HTTPNotFound()

        return {
            "id": book_info["vbid"],
            "title": book_info["title"],
            "cover_image": book_info["resource_links"]["cover_image"],
        }

    @view_config(route_name="vitalsource_api.books.toc")
    def table_of_contents(self):
        book_id = self.request.matchdict["book_id"]

        book_toc = self.vitalsource_service.book_toc(book_id)
        if not book_toc:
            raise HTTPNotFound()

        return book_toc["table_of_contents"]
