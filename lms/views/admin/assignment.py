from dataclasses import asdict

from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.view import view_config, view_defaults

from lms.events import AuditTrailEvent, ModelChange
from lms.models import Assignment, EventType
from lms.security import Permissions


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
        assignment = self._get_or_404()
        return {
            "assignment": assignment,
        }

    @view_config(
        route_name="admin.assignment.dashboard",
        request_method="GET",
        permission=Permissions.STAFF,
    )
    def assignment_dashboard(self):
        assignment = self._get_or_404()
        self.request.registry.notify(
            AuditTrailEvent(
                request=self.request,
                type=EventType.Type.AUDIT_TRAIL,
                data=asdict(
                    ModelChange(
                        model=Assignment.__name__,
                        id=assignment.id,
                        action="view_dashboard",
                        source="admin_pages",
                        userid=self.request.identity.userid,
                        changes={},
                    )
                ),
            )
        )

        response = HTTPFound(
            location=self.request.route_url("dashboard.assignment", id_=assignment.id),
        )
        return response

    def _get_or_404(self) -> Assignment:
        if assignment := self.assignment_service.get_by_id(
            id_=self.request.matchdict["id_"]
        ):
            return assignment

        raise HTTPNotFound()
