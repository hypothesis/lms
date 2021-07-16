from pyramid.view import view_config, view_defaults

from lms.security import Permissions
from lms.services.exceptions import ProxyAPIError
from lms.views.api.vitalsource_sample_data import book_data, toc_data


@view_defaults(renderer="json", permission=Permissions.API)
class VitalSourceAPIViews:
    def __init__(self, request):
        self.request = request

    @view_config(route_name="vitalsource_api.books.info")
    def book_info(self):
        book_id = self.request.matchdict["book_id"]

        # In future this will fetch data from VitalSource.
        if book_id not in book_data:
            raise ProxyAPIError(f"Book {book_id} not found")

        return book_data[book_id]

    @view_config(route_name="vitalsource_api.books.toc")
    def table_of_contents(self):
        book_id = self.request.matchdict["book_id"]

        # In future this will fetch the data from VitalSource using the
        # https://api/vitalsource.com/v4/products/{BOOK_ID}/toc endpoint.
        if book_id not in toc_data:
            raise ProxyAPIError(f"Book {book_id} not found")

        return toc_data[book_id]
