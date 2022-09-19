from marshmallow import validate
from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.view import view_config, view_defaults
from webargs import fields

from lms.models import Organization
from lms.security import Permissions
from lms.services import OrganizationService
from lms.validation._base import PyramidRequestSchema
from lms.views.admin import flash_validation


class NewOrganizationSchema(PyramidRequestSchema):
    location = "form"

    name = fields.Str(required=True, validate=validate.Length(min=1))


@view_defaults(request_method="GET", permission=Permissions.ADMIN)
class AdminOrganizationViews:
    def __init__(self, request):
        self.request = request
        self.organization_service: OrganizationService = request.find_service(
            OrganizationService
        )

    @view_config(
        route_name="admin.organizations",
        request_method="GET",
        renderer="lms:templates/admin/organizations.html.jinja2",
    )
    def organizations(self):  # pragma: no cover
        return {}

    @view_config(
        route_name="admin.organization.new",
        request_method="GET",
        renderer="lms:templates/admin/organization.new.html.jinja2",
    )
    def new_organization(self):  # pragma: no cover
        return {}

    @view_config(
        route_name="admin.organization.new",
        request_method="POST",
        renderer="lms:templates/admin/organization.new.html.jinja2",
    )
    def new_organization_callback(self):
        if flash_validation(self.request, NewOrganizationSchema):
            return {}

        org = self.organization_service.create_organization(
            name=self.request.params["name"].strip()
        )

        return HTTPFound(
            location=self.request.route_url("admin.organization", id_=org.id)
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

        self.organization_service.update_organization(
            org, name=self.request.params.get("name", "").strip()
        )

        return {"org": org}

    @view_config(
        route_name="admin.organization.toggle",
        request_method="POST",
        renderer="lms:templates/admin/organization.html.jinja2",
    )
    def toggle_organization_enabled(self):
        org = self._get_org_or_404(self.request.matchdict["id_"])

        self.organization_service.update_organization(
            org, enabled=self.request.params.get("enabled", "") == "on"
        )

        return {"org": org}

    def _get_org_or_404(self, id_) -> Organization:
        if org := self.organization_service.get_by_id(id_):
            return org

        raise HTTPNotFound()
