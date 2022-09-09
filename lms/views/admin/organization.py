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
    def org_detail(self):
        public_id = self.request.matchdict["public_id"]
        return {
            "org": self.organization_service.get_by_public_id(public_id),
            "public_id": public_id,
        }
