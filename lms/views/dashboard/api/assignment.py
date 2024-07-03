from marshmallow import fields, validate
from pyramid.view import view_config

from lms.js_config_types import (
    APIAssignment,
    APIAssignments,
    APICourse,
)
from lms.models import Assignment
from lms.security import Permissions
from lms.services.h_api import HAPI
from lms.views.dashboard.pagination import PaginationParametersMixin, get_page


class ListAssignmentsSchema(PaginationParametersMixin):
    """Query parameters to fetch a list of assignments."""

    course_id = fields.Integer(required=False, validate=validate.Range(min=1))
    """Return assignments that belong to the course with this ID."""


class AssignmentViews:
    def __init__(self, request) -> None:
        self.request = request
        self.h_api = request.find_service(HAPI)
        self.assignment_service = request.find_service(name="assignment")
        self.dashboard_service = request.find_service(name="dashboard")

    @view_config(
        route_name="api.dashboard.assignments",
        request_method="GET",
        renderer="json",
        permission=Permissions.DASHBOARD_VIEW,
        schema=ListAssignmentsSchema,
    )
    def assignments(self) -> APIAssignments:
        assignments = self.assignment_service.get_assignments(
            h_userid=self.request.user.h_userid if self.request.user else None,
            course_id=self.request.parsed_params.get("course_id"),
        )
        assignments, pagination = get_page(
            self.request, assignments, [Assignment.title, Assignment.id]
        )
        return {
            "assignments": [
                APIAssignment(id=assignment.id, title=assignment.title)
                for assignment in assignments
            ],
            "pagination": pagination,
        }

    @view_config(
        route_name="api.dashboard.assignment",
        request_method="GET",
        renderer="json",
        permission=Permissions.DASHBOARD_VIEW,
    )
    def assignment(self) -> APIAssignment:
        assignment = self.dashboard_service.get_request_assignment(self.request)
        return APIAssignment(
            id=assignment.id,
            title=assignment.title,
            course=APICourse(id=assignment.course.id, title=assignment.course.lms_name),
        )
