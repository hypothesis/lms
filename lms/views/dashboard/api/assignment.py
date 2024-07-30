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

    course_ids = fields.List(
        fields.Integer(validate=validate.Range(min=1)), data_key="course_id"
    )
    """Return users that belong to these course IDs."""

    h_userids = fields.List(fields.Str(), data_key="h_userid")
    """Return metrics for these users only."""

    public_id = fields.Str()
    """Return only the assignments which belong to this organization. For staff member only."""


class AssignmentsMetricsSchema(PyramidRequestSchema):
    """Query parameters to fetch metrics for assignments."""

    location = "querystring"

    h_userids = fields.List(fields.Str(), data_key="h_userid")
    """Return metrics for these users only."""

    assignment_ids = fields.List(fields.Integer(), data_key="assignment_id")
    """Return metrics for these assignments only."""

    public_id = fields.Str()
    """Return only the assignments which belong to this organization. For staff member only."""


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
        filter_by_h_userids = self.request.parsed_params.get("h_userids")
        admin_organizations = self.dashboard_service.get_request_admin_organizations(
            self.request
        )

        assignments = self.assignment_service.get_assignments(
            admin_organization_ids=[org.id for org in admin_organizations],
            instructor_h_userid=self.request.user.h_userid
            if self.request.user
            else None,
            course_ids=self.request.parsed_params.get("course_ids"),
            h_userids=filter_by_h_userids,
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
        # pylint:disable=too-many-locals
        current_h_userid = self.request.user.h_userid if self.request.user else None
        filter_by_h_userids = self.request.parsed_params.get("h_userids")
        filter_by_assignment_ids = self.request.parsed_params.get("assignment_ids")
        admin_organizations = self.dashboard_service.get_request_admin_organizations(
            self.request
        )

        course = self.dashboard_service.get_request_course(self.request)
        course_students = self.request.db.scalars(
            self.user_service.get_users(
                course_ids=[course.id],
                role_scope=RoleScope.COURSE,
                role_type=RoleType.LEARNER,
                instructor_h_userid=current_h_userid,
                admin_organization_ids=[org.id for org in admin_organizations],
                h_userids=filter_by_h_userids,
            )
        ).all()
        assignments_query = self.assignment_service.get_assignments(
            admin_organization_ids=[org.id for org in admin_organizations],
            course_ids=[course.id],
            instructor_h_userid=current_h_userid,
            h_userids=filter_by_h_userids,
        )
        if filter_by_assignment_ids:
            assignments_query = assignments_query.where(
                Assignment.id.in_(filter_by_assignment_ids)
            )
        assignments = self.request.db.scalars(assignments_query).all()

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
