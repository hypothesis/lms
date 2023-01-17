from marshmallow import validate
from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.view import view_config, view_defaults
from webargs import fields

from lms.events import AuditTrailEvent
from lms.models import Organization
from lms.models.public_id import InvalidPublicId
from lms.security import Permissions
from lms.services import OrganizationService
from lms.services.organization import InvalidOrganizationParent
from lms.validation._base import PyramidRequestSchema
from lms.views.admin import flash_validation
from lms.views.admin._schemas import EmptyStringInt


class SearchOrganizationSchema(PyramidRequestSchema):
    location = "form"

    # Max value for postgres `integer` type
    id = EmptyStringInt(required=False, validate=validate.Range(max=2147483647))
    name = fields.Str(required=False)
    public_id = fields.Str(required=False)
    guid = fields.Str(required=False)


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

    @view_config(route_name="admin.organization", request_method="POST")
    def update_organization(self):
        org = self._get_org_or_404(self.request.matchdict["id_"])

        self.organization_service.update_organization(
            org,
            name=self.request.params.get("name", "").strip(),
            notes=self.request.params.get("hypothesis.notes", "").strip(),
        )
        self.request.session.flash("Updated organization", "messages")

        return HTTPFound(
            location=self.request.route_url("admin.organization", id_=org.id)
        )

    @view_config(route_name="admin.organization.move_org", request_method="POST")
    def move_organization(self):
        org = self._get_org_or_404(self.request.matchdict["id_"])

        try:
            self.organization_service.update_organization(
                org,
                parent_public_id=self.request.params.get("parent_public_id", "").strip()
                or None,
            )
            self.request.session.flash("Moved organization", "messages")
        except (InvalidPublicId, InvalidOrganizationParent) as err:
            self.request.session.flash(
                f"Could not move organization id: {err}", "errors"
            )

        return HTTPFound(
            location=self.request.route_url("admin.organization", id_=org.id)
        )

    @view_config(route_name="admin.organization.toggle", request_method="POST")
    def toggle_organization_enabled(self):
        org = self._get_org_or_404(self.request.matchdict["id_"])

        self.organization_service.update_organization(
            org, enabled=self.request.params.get("enabled", "") == "on"
        )

        AuditTrailEvent.notify(self.request, org)
        self.request.session.flash("Updated organization", "messages")

        return HTTPFound(
            location=self.request.route_url("admin.organization", id_=org.id)
        )

    @view_config(
        route_name="admin.organizations",
        request_method="POST",
        renderer="lms:templates/admin/organizations.html.jinja2",
    )
    def search(self):
        if flash_validation(self.request, SearchOrganizationSchema):
            return {}

        try:
            orgs = self.organization_service.search(
                name=self.request.params.get("name", "").strip(),
                id_=self.request.params.get("id", "").strip(),
                public_id=self.request.params.get("public_id", "").strip(),
                guid=self.request.params.get("guid", "").strip(),
            )
        except InvalidPublicId as err:
            self.request.session.flash(str(err), "errors")
            orgs = []

        return {"organizations": orgs}

    def _get_org_or_404(self, id_) -> Organization:
        if org := self.organization_service.get_by_id(id_):
            return org

        raise HTTPNotFound()
