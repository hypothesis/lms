from marshmallow import fields, validate
from pyramid.view import view_config

from lms.js_config_types import (
    AnnotationMetrics,
    APIAssignment,
    APIAssignments,
    APICourse,
    APIStudent,
    APIStudents,
)
from lms.models import Assignment, RoleScope, RoleType
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

    @view_config(
        route_name="api.dashboard.assignment.stats",
        request_method="GET",
        renderer="json",
        permission=Permissions.DASHBOARD_VIEW,
    )
    def assignment_stats(self) -> APIStudents:
        """Fetch the stats for one particular assignment."""
        assignment = self.dashboard_service.get_request_assignment(self.request)
        stats = self.h_api.get_annotation_counts(
            [g.authority_provided_id for g in assignment.groupings],
            group_by="user",
            resource_link_id=assignment.resource_link_id,
        )
        # Organize the H stats by userid for quick access
        stats_by_user = {s["userid"]: s for s in stats}
        students: list[APIStudent] = []

        # Iterate over all the students we have in the DB
        for user in self.assignment_service.get_members(
            assignment, role_scope=RoleScope.COURSE, role_type=RoleType.LEARNER
        ):
            if s := stats_by_user.get(user.h_userid):
                # We seen this student in H, get all the data from there
                students.append(
                    APIStudent(
                        h_userid=user.h_userid,
                        lms_id=user.user_id,
                        display_name=s["display_name"],
                        annotation_metrics=AnnotationMetrics(
                            annotations=s["annotations"],
                            replies=s["replies"],
                            last_activity=s["last_activity"],
                        ),
                    )
                )
            else:
                # We haven't seen this user H,
                # use LMS DB's data and set 0s for all annotation related fields.
                students.append(
                    APIStudent(
                        h_userid=user.h_userid,
                        lms_id=user.user_id,
                        display_name=user.display_name,
                        annotation_metrics=AnnotationMetrics(
                            annotations=0, replies=0, last_activity=None
                        ),
                    )
                )

        return {"students": students}
