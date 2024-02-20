from datetime import datetime

from marshmallow import validate
from pyramid.httpexceptions import HTTPBadRequest, HTTPFound, HTTPNotFound
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


@view_defaults(request_method="GET", permission=Permissions.ADMIN)
class AdminAssignmentViews:
    def __init__(self, request) -> None:
        self.request = request
        self.assignment_service = request.find_service(name="assignment")

    @view_config(
        route_name="admin.assignment",
        request_method="GET",
        renderer="lms:templates/admin/assignment/show.html.jinja2",
        permission=Permissions.STAFF,
    )
    def show(self):
        assignment_id = self.request.matchdict["id_"]
        assignment = self._get_or_404(assignment_id)

        return {
            "assignment": assignment,
        }

    def _get_or_404(self, id_) -> Organization:
        if assignment := self.assignment_service.get_by_id(id_=id_):
            return assignment

        raise HTTPNotFound()
