import logging
from datetime import datetime

from marshmallow import fields, validate
from pyramid.view import view_config

from lms.js_config_types import (
    AnnotationMetrics,
    APIStudent,
    APIStudents,
    AutoGradingGrade,
)
from lms.models import Assignment, RoleScope, RoleType, User
from lms.security import Permissions
from lms.services import UserService
from lms.services.auto_grading import AutoGradingService
from lms.services.h_api import HAPI
from lms.validation._base import PyramidRequestSchema
from lms.views.dashboard.pagination import PaginationParametersMixin, get_page

LOG = logging.getLogger(__name__)


class ListUsersSchema(PaginationParametersMixin):
    """Query parameters to fetch a list of users."""

    course_ids = fields.List(
        fields.Integer(validate=validate.Range(min=1)), data_key="course_id"
    )
    """Return users that belong to these course IDs."""

    assignment_ids = fields.List(
        fields.Integer(validate=validate.Range(min=1)), data_key="assignment_id"
    )
    """Return users that belong to the assignment with these IDs."""

    public_id = fields.Str()
    """Return only the users which belong to this organization. For staff member only."""

    segment_authority_provided_ids = fields.List(
        fields.Str(), data_key="segment_authority_provided_id"
    )
    """Return only the users which belong to this segment (group or section)."""


class UsersMetricsSchema(PyramidRequestSchema):
    """Query parameters to fetch metrics for users."""

    location = "querystring"

    assignment_id = fields.Integer(required=True, validate=validate.Range(min=1))
    """Return users that belong to the assignment with this ID."""

    h_userids = fields.List(fields.Str(), data_key="h_userid")
    """Return metrics for these users only."""

    public_id = fields.Str()
    """Return only the users which belong to this organization. For staff member only."""

    segment_authority_provided_ids = fields.List(
        fields.Str(), data_key="segment_authority_provided_id"
    )
    """Return only the users which belong to this segment (group or section)."""


class UserViews:
    def __init__(self, request) -> None:
        self.request = request
        self.assignment_service = request.find_service(name="assignment")
        self.dashboard_service = request.find_service(name="dashboard")
        self.h_api: HAPI = request.find_service(HAPI)
        self.user_service: UserService = request.find_service(UserService)
        self.auto_grading_service: AutoGradingService = request.find_service(
            AutoGradingService
        )

    @view_config(
        route_name="api.dashboard.students",
        request_method="GET",
        renderer="json_iso_utc",
        permission=Permissions.DASHBOARD_VIEW,
        schema=ListUsersSchema,
    )
    def students(self) -> APIStudents:
        admin_organizations = self.dashboard_service.get_request_admin_organizations(
            self.request
        )

        students_query = self.user_service.get_users(
            role_scope=RoleScope.COURSE,
            role_type=RoleType.LEARNER,
            instructor_h_userid=self.request.user.h_userid
            if self.request.user
            else None,
            admin_organization_ids=[org.id for org in admin_organizations],
            course_ids=self.request.parsed_params.get("course_ids"),
            assignment_ids=self.request.parsed_params.get("assignment_ids"),
            segment_authority_provided_ids=self.request.parsed_params.get(
                "segment_authority_provided_ids"
            ),
        )
        students, pagination = get_page(
            self.request, students_query, [User.display_name, User.id]
        )

        return {
            "students": [
                APIStudent(
                    h_userid=s.h_userid, lms_id=s.user_id, display_name=s.display_name
                )
                for s in students
            ],
            "pagination": pagination,
        }

    @view_config(
        route_name="api.dashboard.students.metrics",
        request_method="GET",
        renderer="json_iso_utc",
        permission=Permissions.DASHBOARD_VIEW,
        schema=UsersMetricsSchema,
    )
    def students_metrics(self) -> APIStudents:
        """Fetch the stats for one particular assignment."""
        assignment = self.dashboard_service.get_request_assignment(self.request)

        request_segment_authority_provided_ids = self.request.parsed_params.get(
            "segment_authority_provided_ids"
        )

        assignment_groupings_authority_provided_ids: list[str] = [
            g.authority_provided_id for g in assignment.groupings
        ]
        if request_segment_authority_provided_ids:
            assignment_groupings_authority_provided_ids = [
                g
                for g in assignment_groupings_authority_provided_ids
                if g in request_segment_authority_provided_ids
            ]

        request_h_userids = self.request.parsed_params.get("h_userids")
        stats = self.h_api.get_annotation_counts(
            assignment_groupings_authority_provided_ids,
            group_by="user",
            resource_link_ids=[assignment.resource_link_id],
            h_userids=request_h_userids,
        )
        # Organize the H stats by userid for quick access
        stats_by_user = {s["userid"]: s for s in stats}
        students: list[APIStudent] = []

        admin_organizations = self.dashboard_service.get_request_admin_organizations(
            self.request
        )

        users_query = self.user_service.get_users(
            role_scope=RoleScope.COURSE,
            role_type=RoleType.LEARNER,
            assignment_ids=[assignment.id],
            # Users the current user has access to see
            instructor_h_userid=self.request.user.h_userid
            if self.request.user
            else None,
            admin_organization_ids=[org.id for org in admin_organizations],
            # Users the current user requested
            h_userids=request_h_userids,
            # Only users belonging to these segments
            segment_authority_provided_ids=request_segment_authority_provided_ids,
        )
        # Iterate over all the students we have in the DB
        for user in self.request.db.scalars(users_query).all():
            if s := stats_by_user.get(user.h_userid):
                # We seen this student in H, get all the data from there
                api_student = APIStudent(
                    h_userid=user.h_userid,
                    lms_id=user.user_id,
                    display_name=s["display_name"],
                    annotation_metrics=AnnotationMetrics(
                        annotations=s["annotations"] + s["page_notes"],
                        replies=s["replies"],
                        last_activity=datetime.fromisoformat(s["last_activity"]),
                    ),
                )
            else:
                # We haven't seen this user H,
                # use LMS DB's data and set 0s for all annotation related fields.
                api_student = APIStudent(
                    h_userid=user.h_userid,
                    lms_id=user.user_id,
                    display_name=user.display_name,
                    annotation_metrics=AnnotationMetrics(
                        annotations=0, replies=0, last_activity=None
                    ),
                )
            students.append(api_student)

        if assignment.auto_grading_config:
            students = self._add_auto_grading_data(assignment, students)

        return {"students": students}

    def _add_auto_grading_data(
        self, assignment: Assignment, api_students: list[APIStudent]
    ) -> list[APIStudent]:
        """Augment APIStudent with auto-grading data."""
        last_sync_grades = self.auto_grading_service.get_last_grades(assignment)

        for api_student in api_students:
            auto_grading_grade: AutoGradingGrade = {
                "current_grade": self.auto_grading_service.calculate_grade(
                    assignment.auto_grading_config,
                    api_student["annotation_metrics"],
                ),
                "last_grade": None,
                "last_grade_date": None,
            }
            if last_grade := last_sync_grades.get(api_student["h_userid"]):
                auto_grading_grade["last_grade"] = last_grade.grade
                auto_grading_grade["last_grade_date"] = last_grade.updated

            api_student["auto_grading_grade"] = auto_grading_grade

        return api_students
