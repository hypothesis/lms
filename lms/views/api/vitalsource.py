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
        self.svc: VitalSourceService = request.find_service(VitalSourceService)

    @view_config(route_name="vitalsource_api.books.info", schema=_BookSchema)
    def book_info(self):
        return self.svc.get_book_info(self.request.matchdict["book_id"])

    @view_config(route_name="vitalsource_api.books.toc", schema=_BookSchema)
    def table_of_contents(self):
        return self.svc.get_table_of_contents(self.request.matchdict["book_id"])

    @view_config(route_name="vitalsource_api.launch_url")
    def launch_url(self):
        # The URL is in a `via_url` property, so it can be used the same way
        # as assignments that do use Via. We should rename this to something
        # more generic.
        return {
            "via_url": self.svc.get_sso_redirect(
                user_reference=self.request.params["user_reference"],
                document_url=self.request.params["document_url"],
            )
        }
