import logging
from datetime import datetime
from typing import TYPE_CHECKING

from marshmallow import fields, validate
from pyramid.view import view_config
from sqlalchemy import Select, true

from lms.js_config_types import (
    AnnotationMetrics,
    APIRoster,
    APIStudent,
    APIStudents,
    AutoGradingGrade,
    CheckpointMetrics,
    RosterEntry,
)
from lms.models import Assignment, LMSUser, RoleScope, RoleType
from lms.security import Permissions
from lms.services import UserService
from lms.services.auto_grading import AutoGradingService
from lms.services.h_api import HAPI
from lms.validation._base import PyramidRequestSchema
from lms.views.dashboard.pagination import PaginationParametersMixin, get_page

LOG = logging.getLogger(__name__)

if TYPE_CHECKING:
    from lms.services.dashboard import DashboardService


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
        self.dashboard_service: DashboardService = request.find_service(
            name="dashboard"
        )
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
        _, students_query = self._students_query(
            assignment_ids=self.request.parsed_params.get("assignment_ids"),
            segment_authority_provided_ids=self.request.parsed_params.get(
                "segment_authority_provided_ids"
            ),
        )

        students, pagination = get_page(
            self.request, students_query, [LMSUser.display_name, LMSUser.id]
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
    def students_metrics(self) -> APIRoster:
        """Fetch the stats for one particular assignment."""
        assignment = self.dashboard_service.get_request_assignment(
            self.request, self.request.parsed_params["assignment_id"]
        )

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
        use_checkpoint = assignment.checkpoint_enabled and assignment.document_uri
        stats = self.h_api.get_annotation_counts(
            assignment_groupings_authority_provided_ids,
            group_by="user",
            resource_link_ids=[assignment.resource_link_id],
            h_userids=request_h_userids,
            document_uri=assignment.document_uri if use_checkpoint else None,
            due_date=assignment.due_date if use_checkpoint else None,
        )
        # Organize the H stats by userid for quick access
        stats_by_user = {s["userid"]: s for s in stats}
        checkpoint_revealed = False
        checkpoint_reveal_date = None
        if use_checkpoint and stats:
            checkpoint_revealed = stats[0]["checkpoint_revealed"]
            checkpoint_reveal_date = stats[0]["checkpoint_reveal_date"]
        students: list[RosterEntry] = []

        roster_last_updated, users_query = self._students_query(
            assignment_ids=[assignment.id],
            segment_authority_provided_ids=request_segment_authority_provided_ids,
            h_userids=request_h_userids,
        )
        # Iterate over all the students we have in the DB
        for roster_data in self.request.db.execute(users_query).all():
            user, active = roster_data
            if s := stats_by_user.get(user.h_userid):
                # We seen this student in H, get all the data from there
                api_student = RosterEntry(
                    active=active,
                    h_userid=user.h_userid,
                    lms_id=user.user_id,
                    display_name=s["display_name"],
                    annotation_metrics=AnnotationMetrics(
                        annotations=s["annotations"] + s["page_notes"],
                        replies=s["replies"],
                        last_activity=datetime.fromisoformat(s["last_activity"]),
                    ),
                )
                if use_checkpoint:
                    api_student["checkpoint_metrics"] = self._checkpoint_metrics(s)
            else:
                # We haven't seen this user H,
                # use LMS DB's data and set 0s for all annotation related fields.
                api_student = RosterEntry(
                    active=active,
                    h_userid=user.h_userid,
                    lms_id=user.user_id,
                    display_name=user.display_name,
                    annotation_metrics=AnnotationMetrics(
                        annotations=0, replies=0, last_activity=None
                    ),
                )
                if use_checkpoint:
                    empty = AnnotationMetrics(
                        annotations=0, replies=0, last_activity=None
                    )
                    api_student["checkpoint_metrics"] = CheckpointMetrics(
                        revealed=checkpoint_revealed,
                        reveal_date=(
                            datetime.fromisoformat(checkpoint_reveal_date)
                            if checkpoint_reveal_date
                            else None
                        ),
                        checkpoint=empty,
                        due_date=empty,
                    )
            students.append(api_student)

        if assignment.auto_grading_config:
            students = self._add_auto_grading_data(assignment, students)

        return APIRoster(students=students, last_updated=roster_last_updated)

    @staticmethod
    def _checkpoint_metrics(stats: dict) -> CheckpointMetrics:
        """
        Split one h stats row into "checkpoint" and "due_date" buckets.

        h returns `checkpoint_*` counts (created at/before reveal_date) plus
        the totals (bounded by the due_date sent in the request). The
        "due_date" bucket — created after reveal_date, at/before due_date —
        is not computed by h directly; it's derived here by subtraction.
        """
        total_annotations = stats["annotations"] + stats["page_notes"]
        total_replies = stats["replies"]
        checkpoint_annotations = (
            stats["checkpoint_annotations"] + stats["checkpoint_page_notes"]
        )
        checkpoint_replies = stats["checkpoint_replies"]

        due_date_annotations = total_annotations - checkpoint_annotations
        due_date_replies = total_replies - checkpoint_replies
        
        due_date_last_activity = (
            datetime.fromisoformat(stats["last_activity"])
            if (due_date_annotations + due_date_replies) > 0 and stats["last_activity"]
            else None
        )

        return CheckpointMetrics(
            revealed=stats["checkpoint_revealed"],
            reveal_date=(
                datetime.fromisoformat(stats["checkpoint_reveal_date"])
                if stats["checkpoint_reveal_date"]
                else None
            ),
            checkpoint=AnnotationMetrics(
                annotations=checkpoint_annotations,
                replies=checkpoint_replies,
                last_activity=(
                    datetime.fromisoformat(stats["checkpoint_last_activity"])
                    if stats["checkpoint_last_activity"]
                    else None
                ),
            ),
            due_date=AnnotationMetrics(
                annotations=due_date_annotations,
                replies=due_date_replies,
                last_activity=due_date_last_activity,
            ),
        )

    def _add_auto_grading_data(
        self, assignment: Assignment, api_students: list[RosterEntry]
    ) -> list[RosterEntry]:
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

            # Checkpoint/due_date grades are informational only — there's no
            # mechanism to sync more than one grade per assignment to the
            # LMS gradebook, so these never get a `last_grade`.
            if checkpoint_metrics := api_student.get("checkpoint_metrics"):
                checkpoint_metrics["checkpoint_grade"] = (
                    self.auto_grading_service.calculate_grade(
                        assignment.auto_grading_config,
                        checkpoint_metrics["checkpoint"],
                    )
                )
                checkpoint_metrics["due_date_grade"] = (
                    self.auto_grading_service.calculate_grade(
                        assignment.auto_grading_config,
                        checkpoint_metrics["due_date"],
                    )
                )

        return api_students

    def _students_query(
        self,
        assignment_ids: list[int],
        segment_authority_provided_ids: list[str],
        h_userids: list[str] | None = None,
    ) -> tuple[datetime | None, Select[tuple[LMSUser, bool]]]:
        course_ids = self.request.parsed_params.get("course_ids")

        # Roster for specific segments
        if segment_authority_provided_ids:
            # Fetch all the segments to be sure the current user has access to them.
            segments = [
                self.dashboard_service.get_request_segment(
                    self.request, authority_provided_id
                )
                for authority_provided_id in segment_authority_provided_ids
            ]

            return self.dashboard_service.get_segments_roster(
                segments=segments, h_userids=h_userids
            )

        # Single assigment fetch
        if (
            assignment_ids
            and len(assignment_ids) == 1
            and not segment_authority_provided_ids
        ):
            # Fetch the assignment to be sure the current user has access to it.
            assignment = self.dashboard_service.get_request_assignment(
                self.request, assignment_ids[0]
            )
            return self.dashboard_service.get_assignment_roster(
                assignment=assignment, h_userids=h_userids
            )

        # Single course fetch
        if course_ids and len(course_ids) == 1 and not segment_authority_provided_ids:
            # Fetch the course to be sure the current user has access to it.
            course = self.dashboard_service.get_request_course(
                self.request, course_id=course_ids[0]
            )
            return self.dashboard_service.get_course_roster(
                lms_course=course.lms_course, h_userids=h_userids
            )

        admin_organizations = self.dashboard_service.get_request_admin_organizations(
            self.request
        )
        # Full organization fetch
        if not course_ids and not assignment_ids and not segment_authority_provided_ids:
            return None, self.user_service.get_users_for_organization(
                role_scope=RoleScope.COURSE,
                role_type=RoleType.LEARNER,
                h_userids=h_userids,
                # Users the current user has access to see
                instructor_h_userid=self.request.user.h_userid
                if self.request.user
                else None,
                admin_organization_ids=[org.id for org in admin_organizations],
                # For launch data we always add the "active" column as true for compatibility with the roster query.
            ).add_columns(true())

        return None, self.user_service.get_users(
            role_scope=RoleScope.COURSE,
            role_type=RoleType.LEARNER,
            course_ids=self.request.parsed_params.get("course_ids"),
            assignment_ids=assignment_ids,
            # Users the current user has access to see
            instructor_h_userid=self.request.user.h_userid
            if self.request.user
            else None,
            admin_organization_ids=[org.id for org in admin_organizations],
            # Users the current user requested
            h_userids=h_userids,
            # Only users belonging to these segments
            segment_authority_provided_ids=segment_authority_provided_ids,
            # For launch data we always add the "active" column as true for compatibility with the roster query.
        ).add_columns(true())
