from marshmallow import fields, validate
from pyramid.view import view_config, view_defaults

from lms.security import Permissions
from lms.services import VitalSourceService
from lms.validation import PyramidRequestSchema


class _BookSchema(PyramidRequestSchema):
    location = "matchdict"

    book_id = fields.Str(required=True, validate=validate.Regexp(r"^[\dA-Z-]+$"))


@view_defaults(renderer="json", permission=Permissions.API)
class VitalSourceAPIViews:
    def __init__(self, request):
        self.request = request
        self.svc = request.find_service(VitalSourceService)

    @view_config(route_name="vitalsource_api.books.info", schema=_BookSchema)
    def book_info(self):
        return self.svc.get_book_info(self.request.matchdict["book_id"])

    @view_config(route_name="vitalsource_api.books.toc", schema=_BookSchema)
    def table_of_contents(self):
        return self.svc.get_table_of_contents(self.request.matchdict["book_id"])
