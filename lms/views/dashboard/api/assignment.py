from marshmallow import fields, validate
from pyramid.view import view_config

from lms.js_config_types import (
    AnnotationMetrics,
    APIAssignment,
    APIAssignments,
    APICourse,
)
from lms.models import Assignment, RoleScope, RoleType
from lms.security import Permissions
from lms.services import UserService
from lms.services.h_api import HAPI
from lms.validation import PyramidRequestSchema
from lms.views.dashboard.pagination import PaginationParametersMixin, get_page


class ListAssignmentsSchema(PaginationParametersMixin):
    """Query parameters to fetch a list of assignments."""

    course_id = fields.Integer(required=False, validate=validate.Range(min=1))
    """Return assignments that belong to the course with this ID."""


class AssignmentsMetricsSchema(PyramidRequestSchema):
    """Query parameters to fetch metrics for assignments."""

    location = "querystring"

    h_userids = fields.List(fields.Str())
    """Return metrics for these users only."""


class AssignmentViews:
    def __init__(self, request) -> None:
        self.request = request
        self.h_api = request.find_service(HAPI)
        self.assignment_service = request.find_service(name="assignment")
        self.dashboard_service = request.find_service(name="dashboard")
        self.course_service = request.find_service(name="course")
        self.user_service: UserService = request.find_service(UserService)

    @view_config(
        route_name="api.dashboard.assignments",
        request_method="GET",
        renderer="json",
        permission=Permissions.DASHBOARD_VIEW,
        schema=ListAssignmentsSchema,
    )
    def assignments(self) -> APIAssignments:
        assignments = self.assignment_service.get_assignments(
            instructor_h_userid=self.request.user.h_userid
            if self.request.user
            else None,
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
        route_name="api.dashboard.course.assignments.metrics",
        request_method="GET",
        renderer="json",
        permission=Permissions.DASHBOARD_VIEW,
        schema=AssignmentsMetricsSchema,
    )
    def course_assignments_metrics(self) -> APIAssignments:
        current_h_userid = self.request.user.h_userid if self.request.user else None
        filter_by_h_userids = self.request.parsed_params.get("h_userids")
        course = self.dashboard_service.get_request_course(self.request)
        course_students = self.request.db.scalars(
            self.user_service.get_users(
                course_id=course.id,
                role_scope=RoleScope.COURSE,
                role_type=RoleType.LEARNER,
                instructor_h_userid=current_h_userid,
                h_userids=filter_by_h_userids,
            )
        ).all()
        assignments = self.request.db.scalars(
            self.assignment_service.get_assignments(
                course_id=course.id,
                instructor_h_userid=current_h_userid,
                h_userids=filter_by_h_userids,
            )
        ).all()

        stats = self.h_api.get_annotation_counts(
            # Annotations in the course group and any children
            [course.authority_provided_id]
            + [child.authority_provided_id for child in course.children],
            group_by="assignment",
            h_userids=[s.h_userid for s in course_students],
        )
        # Organize the H stats by assignment ID for quick access
        stats_by_assignment = {s["assignment_id"]: s for s in stats}
        response_assignments: list[APIAssignment] = []

        # Same course for all these assignments
        api_course = APICourse(id=course.id, title=course.lms_name)
        for assignment in assignments:
            if h_stats := stats_by_assignment.get(assignment.resource_link_id):
                metrics = AnnotationMetrics(
                    annotations=h_stats["annotations"],
                    replies=h_stats["replies"],
                    last_activity=h_stats["last_activity"],
                )
            else:
                # Assignment with no annos, zeroing the stats
                metrics = AnnotationMetrics(
                    annotations=0, replies=0, last_activity=None
                )

            response_assignments.append(
                APIAssignment(
                    id=assignment.id,
                    title=assignment.title,
                    course=api_course,
                    annotation_metrics=metrics,
                )
            )

        return {"assignments": response_assignments}
