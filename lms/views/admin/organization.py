from pyramid.httpexceptions import HTTPNotFound
from pyramid.view import view_config, view_defaults

from lms.models import Organization
from lms.security import Permissions
from lms.services import OrganizationService


@view_defaults(request_method="GET", permission=Permissions.ADMIN)
class AdminOrganizationViews:
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
    def show_organization(self):
        org = self._get_org_or_404(self.request.matchdict["id_"])
        return {"org": org}

    @view_config(
        route_name="admin.organization",
        request_method="POST",
        renderer="lms:templates/admin/organization.html.jinja2",
    )
    def update_organization(self):
        org = self._get_org_or_404(self.request.matchdict["id_"])

        org.name = self.request.params.get("name", "").strip() or None

        org.enabled = self.request.params.get("enabled", "") == "on"

        return {"org": org}

    def _get_org_or_404(self, id_) -> Organization:
        if org := self.organization_service.get_by_id(id_):
            return org

        raise HTTPNotFound()
