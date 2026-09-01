import logging
from collections import defaultdict
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
    PhaseMetrics,
    RosterEntry,
)
from lms.models import Assignment, LMSUser, RoleScope, RoleType
from lms.security import Permissions
from lms.services import UserService
from lms.services.auto_grading import AutoGradingService
from lms.services.h_api import HAPI, AnnotationCounts
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
        # A checkpointed assignment is graded per phase, so ask h to bucket the
        # counts. It needs `document_uri` to find the checkpoint whose reveals
        # delimit them, and `due_date` to close the last one.
        use_phases = bool(assignment.checkpoint_enabled and assignment.document_uri)
        stats = self.h_api.get_annotation_counts(
            assignment_groupings_authority_provided_ids,
            group_by="user_phase" if use_phases else "user",
            resource_link_ids=[assignment.resource_link_id],
            h_userids=request_h_userids,
            document_uri=assignment.document_uri if use_phases else None,
            due_date=assignment.due_date if use_phases else None,
        )
        # Organize the H stats by userid for quick access. Grouping by phase
        # returns several rows per user, one per phase.
        stats_by_user: dict[str, list[AnnotationCounts]] = defaultdict(list)
        for row in stats:
            if userid := row["userid"]:
                stats_by_user[userid].append(row)

        # From h: an assignment can have phases and no grading configs. Used
        # for the students h reports nothing for, who have no rows of their own.
        phase_boundaries = self._phase_boundaries(stats) if use_phases else []
        students: list[RosterEntry] = []

        roster_last_updated, users_query = self._students_query(
            assignment_ids=[assignment.id],
            segment_authority_provided_ids=request_segment_authority_provided_ids,
            h_userids=request_h_userids,
        )
        # Iterate over all the students we have in the DB
        for roster_data in self.request.db.execute(users_query).all():
            user, active = roster_data
            if rows := stats_by_user.get(user.h_userid):
                # We seen this student in H, get all the data from there
                api_student = RosterEntry(
                    active=active,
                    h_userid=user.h_userid,
                    lms_id=user.user_id,
                    display_name=rows[0]["display_name"],
                    annotation_metrics=self._total_metrics(rows),
                )
                if use_phases:
                    api_student["phase_metrics"] = self._phase_metrics(rows)
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
                if use_phases:
                    api_student["phase_metrics"] = self._zeroed_phase_metrics(
                        phase_boundaries
                    )
            students.append(api_student)

        if assignment.auto_grading_config:
            students = self._add_auto_grading_data(assignment, students)

        return APIRoster(students=students, last_updated=roster_last_updated)

    @staticmethod
    def _metrics(row: AnnotationCounts) -> AnnotationMetrics:
        """Read one h row's counts, page notes folded into annotations."""
        return AnnotationMetrics(
            annotations=row["annotations"] + row["page_notes"],
            replies=row["replies"],
            last_activity=(
                datetime.fromisoformat(row["last_activity"])
                if row["last_activity"]
                else None
            ),
        )

    @classmethod
    def _total_metrics(cls, rows: list[AnnotationCounts]) -> AnnotationMetrics:
        """Sum a student's rows.

        One row unless we asked h to bucket by phase, in which case the totals
        are the phases added up. Note they only cover activity up to the due
        date, because that bounds every count h returns for the request.
        """
        per_row = [cls._metrics(row) for row in rows]
        activity = [m["last_activity"] for m in per_row if m["last_activity"]]

        return AnnotationMetrics(
            annotations=sum(m["annotations"] for m in per_row),
            replies=sum(m["replies"] for m in per_row),
            last_activity=max(activity) if activity else None,
        )

    @classmethod
    def _phase_metrics(cls, rows: list[AnnotationCounts]) -> list[PhaseMetrics]:
        """One entry per grading phase, in phase order.

        h buckets the annotations and reports where each phase ends, so nothing
        here needs to know the checkpoint's reveal dates.
        """
        ordered = sorted(rows, key=lambda row: row["phase"])
        boundaries = [
            datetime.fromisoformat(row["ends_at"]) if row["ends_at"] else None
            for row in ordered
        ]

        return cls._build_phases(
            boundaries, [cls._metrics(row) for row in ordered], ordered[0]["phase"]
        )

    @staticmethod
    def _phase_boundaries(stats: list[AnnotationCounts]) -> list[datetime | None]:
        """When each phase of the assignment closes, as h reports it.

        A group set reveals per group, so a phase can close at different times
        for different students; the earliest is the one that has definitely
        happened.
        """
        ends_at: dict[int, datetime | None] = {}
        for row in stats:
            end = datetime.fromisoformat(row["ends_at"]) if row["ends_at"] else None
            current = ends_at.get(row["phase"], end)
            ends_at[row["phase"]] = (
                min(current, end) if current and end else current or end
            )

        return [ends_at[phase] for phase in sorted(ends_at)]

    @classmethod
    def _zeroed_phase_metrics(
        cls, boundaries: list[datetime | None]
    ) -> list[PhaseMetrics]:
        """Build the phases of a student h reports no annotations for.

        Sent rather than omitted so a started phase shows a 0 instead of a
        blank. The boundaries come from what h reported for the other students,
        since this one has no rows of their own to read them from -- close
        enough except on a group set part-way through its reveals.
        """
        return cls._build_phases(
            boundaries,
            [
                AnnotationMetrics(annotations=0, replies=0, last_activity=None)
                for _ in boundaries
            ],
        )

    @classmethod
    def _build_phases(
        cls,
        boundaries: list[datetime | None],
        metrics: list[AnnotationMetrics],
        first_phase: int = 1,
    ) -> list[PhaseMetrics]:
        """Pair each phase's boundary with its metrics, marking which have begun."""
        now = datetime.utcnow()  # noqa: DTZ003

        return [
            PhaseMetrics(
                phase=first_phase + index,
                ends_at=ends_at,
                started=cls._phase_started(boundaries, index, now),
                metrics=phase_metrics,
            )
            for index, (ends_at, phase_metrics) in enumerate(
                zip(boundaries, metrics, strict=True)
            )
        ]

    def _add_auto_grading_data(
        self, assignment: Assignment, api_students: list[RosterEntry]
    ) -> list[RosterEntry]:
        """Augment APIStudent with auto-grading data."""
        last_sync_grades = self.auto_grading_service.get_last_grades(assignment)
        # Phase N is graded against the config at position N. A shorter chain
        # leaves the later phases ungraded, which `zip` does by stopping at the
        # shorter side.
        configs = self.assignment_service.get_auto_grading_configs(assignment)

        for api_student in api_students:
            phases = api_student.get("phase_metrics") or []
            for phase_metrics, config in zip(phases, configs, strict=False):
                phase_metrics["grade"] = self.auto_grading_service.calculate_grade(
                    config, phase_metrics["metrics"]
                )

            auto_grading_grade: AutoGradingGrade = {
                # Only the final grade is ever synced; the per-phase grades feed
                # into it but are never sent on their own.
                "current_grade": self._final_grade(phases)
                if phases
                else self.auto_grading_service.calculate_grade(
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

    @classmethod
    def _final_grade(cls, phases: list[PhaseMetrics]) -> float:
        """Average the grades of the phases that have started.

        `ends_at` is naive UTC, matching lms's other `utcnow()` comparisons.
        """
        grades = [
            phase_metrics["grade"]
            for phase_metrics in phases
            if "grade" in phase_metrics and phase_metrics["started"]
        ]

        return round(sum(grades) / len(grades), 3)

    @staticmethod
    def _phase_started(
        boundaries: list[datetime | None], index: int, now: datetime
    ) -> bool:
        """Whether the phase at `index` has begun.

        A phase starts when the previous one ends, so a previous boundary that
        is unset (an unrevealed checkpoint) or still ahead (a scheduled reveal,
        or a due date yet to pass) means this one hasn't.
        """
        if index == 0:
            return True

        previous_end = boundaries[index - 1]

        return previous_end is not None and previous_end <= now

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
