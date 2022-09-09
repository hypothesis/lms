from pyramid.view import view_config, view_defaults

from lms.security import Permissions
from lms.services import OrganizationService


@view_defaults(request_method="GET", permission=Permissions.ADMIN)
class AdminLTIRegistrationViews:
    def __init__(self, request):
        self.request = request
        self.organization_service: OrganizationService = request.find_service(
            OrganizationService
        )

    @view_config(
        route_name="admin.organization",
        request_method="GET",
        renderer="lms:templates/admin/organization.html.jinja2",
    )
    def org_details(self):
        public_id = self.request.matchdict["public_id"]
        return {
            "org": self.organization_service.get_by_public_id(public_id),
        }

    @view_config(
        route_name="admin.organization",
        request_method="POST",
        renderer="lms:templates/admin/organization.html.jinja2",
    )
    def org_update(self):
        public_id = self.request.matchdict["public_id"]
        org = self.organization_service.get_by_public_id(public_id)

        if name := self.request.params.get("name", "").strip():
            org.name = name

        return {"org": org}
