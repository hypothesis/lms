from datetime import datetime

from marshmallow import validate
from pyramid.httpexceptions import HTTPBadRequest, HTTPFound, HTTPNotFound
from pyramid.view import view_config, view_defaults
from webargs import fields

from lms.events import AuditTrailEvent
from lms.models import Organization
from lms.models.public_id import InvalidPublicId
from lms.security import Permissions
from lms.services import HubSpotService, OrganizationService
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
    def __init__(self, request) -> None:
        self.request = request
        self.organization_service: OrganizationService = request.find_service(
            OrganizationService
        )
        self.hubspot_service: HubSpotService = request.find_service(HubSpotService)

    @view_config(
        route_name="admin.organizations",
        request_method="GET",
        renderer="lms:templates/admin/organization/search.html.jinja2",
        permission=Permissions.STAFF,
    )
    def organizations(self):  # pragma: no cover
        return {}

    @view_config(
        route_name="admin.organization.new",
        request_method="GET",
        renderer="lms:templates/admin/organization/new.html.jinja2",
    )
    def new_organization(self):  # pragma: no cover
        return {}

    @view_config(
        route_name="admin.organization.new",
        request_method="POST",
        renderer="lms:templates/admin/organization/new.html.jinja2",
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
        renderer="lms:templates/admin/organization/show.html.jinja2",
        permission=Permissions.STAFF,
    )
    @view_config(
        route_name="admin.organization.section",
        request_method="GET",
        renderer="lms:templates/admin/organization/show.html.jinja2",
        permission=Permissions.STAFF,
    )
    def show_organization(self):
        org = self._get_org_or_404(self.request.matchdict["id_"])

        return {
            "org": org,
            "company": self.hubspot_service.get_company(org.public_id),
            "hierarchy_root": self.organization_service.get_hierarchy_root(org.id),
            "sort_by_name": lambda items: sorted(
                items, key=lambda value: value.name or ""
            ),
        }

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
        # Make sure the top level org exists, 404 otherwise
        request_org_id = self.request.matchdict["id_"]
        for org_id in self.organization_service.get_hierarchy_ids(request_org_id):
            org = self.organization_service.get_by_id(org_id)
            self.organization_service.update_organization(
                org, enabled=self.request.params.get("enabled", "") == "on"
            )
            AuditTrailEvent.notify(self.request, org)
            self.request.session.flash(
                f"Updated organization {org.public_id}", "messages"
            )

        return HTTPFound(
            location=self.request.route_url(
                "admin.organization.section", id_=request_org_id, section="danger"
            )
        )

    @view_config(
        route_name="admin.organizations",
        request_method="POST",
        renderer="lms:templates/admin/organization/search.html.jinja2",
        permission=Permissions.STAFF,
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

    @view_config(
        route_name="admin.organization.section",
        match_param="section=usage",
        request_method="POST",
        permission=Permissions.STAFF,
        renderer="lms:templates/admin/organization/usage.html.jinja2",
    )
    def usage(self):
        org = self._get_org_or_404(self.request.matchdict["id_"])
        try:
            since = datetime.fromisoformat(self.request.params["since"])
            until = datetime.fromisoformat(self.request.params["until"])
        except ValueError as exc:
            raise HTTPBadRequest(
                "Times must be in ISO 8601 format, for example: '2023-02-27T00:00:00'."
            ) from exc

        if until <= since:
            raise HTTPBadRequest(
                "The 'since' time must be earlier than the 'until' time."
            )

        if since < datetime(2023, 1, 1):
            raise HTTPBadRequest("Usage reports can only be generated since 2023")

        try:
            report = self.organization_service.usage_report(org, since, until)
        except ValueError as exc:
            self.request.session.flash(
                f"There was a problem generating the report: {exc}", "errors"
            )
            report = []

        return {
            "org": org,
            "since": since,
            "until": until,
            "report": report,
            "company": self.hubspot_service.get_company(org.public_id),
        }

    def _get_org_or_404(self, id_) -> Organization:
        if org := self.organization_service.get_by_id(id_):
            return org

        raise HTTPNotFound()
