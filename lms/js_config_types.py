"""
Types of the config exposed to the frontend and API return values.

Making this a top level module to avoid circular dependency problems.
"""

from datetime import datetime
from typing import Literal, NotRequired, TypedDict


class AutoGradingConfig(TypedDict):
    grading_type: Literal["all_or_nothing", "scaled"] | None
    """
    - all_or_nothing: students need to meet a minimum value, making them get
                      either 0% or 100%
    - scaled: students may get a proportional grade based on the amount of
              annotations. If requirement is 4, and they created 3, they'll
              get a 75%
    """

    activity_calculation: Literal["cumulative", "separate"] | None
    """
    - cumulative: both annotations and replies will be counted together for
                  the grade calculation
    - separate: students will have different annotation and reply goals.
    """

    required_annotations: int
    required_replies: int | None


class Pagination(TypedDict):
    next: str | None
    """URL to fetch the next set of results."""


class AnnotationMetrics(TypedDict):
    annotations: int
    replies: int
    last_activity: datetime | None


class CourseMetrics(TypedDict):
    assignments: int
    last_launched: datetime | None


class APICallInfo(TypedDict):
    path: str
    authUrl: NotRequired[str]


class APICourse(TypedDict):
    id: int
    title: str

    course_metrics: NotRequired[CourseMetrics]


class AutoGradingGrade(TypedDict):
    current_grade: float
    """Current auto-grading grade calculated based on the config and current number of annotations."""

    last_grade: float | None
    """Last grade that was succefully sync to the LMS."""

    last_grade_date: datetime | None
    """Time when `last_grade` was synced to the LMS."""


class APIStudent(TypedDict):
    h_userid: str
    """ID of the student in H."""

    lms_id: str
    """ID of the student in the LMS."""

    display_name: str | None

    annotation_metrics: NotRequired[AnnotationMetrics]
    auto_grading_grade: NotRequired[AutoGradingGrade]


class APICourses(TypedDict):
    courses: list[APICourse]

    pagination: NotRequired[Pagination]


class APISegment(TypedDict):
    h_authority_provided_id: str
    name: str


class APIAssignment(TypedDict):
    id: int
    title: str
    created: str
    is_gradable: bool

    course: NotRequired[APICourse]

    sections: NotRequired[list[APISegment]]
    groups: NotRequired[list[APISegment]]

    annotation_metrics: NotRequired[AnnotationMetrics]
    auto_grading_config: NotRequired[AutoGradingConfig]


class APIAssignments(TypedDict):
    assignments: list[APIAssignment]

    pagination: NotRequired[Pagination]


class RosterEntry(APIStudent):
    active: bool
    "Whether or not this student is active in the course/assignment or roster."


class APIRoster(TypedDict):
    students: list[RosterEntry]

    last_updated: datetime | None
    """When was this roster last updated.
    None indicates we don't have roster data, we rely on launches to determine the list of students."""


class APIStudents(TypedDict):
    students: list[APIStudent]

    pagination: NotRequired[Pagination]


class DashboardRoutes(TypedDict):
    assignment: str
    """Fetch a single assigment by ID"""

    students_metrics: str

    course: str
    """Fetch a single course by ID"""

    course_assignments_metrics: str

    courses_metrics: str

    courses: str
    """Paginated endpoint to fetch courses"""
    assignments: str
    """Paginated endpoint to fetch assigments"""
    students: str
    """Paginated endpoint to fetch students"""

    assignment_grades_sync: str
    """Sync grades for a given assignment"""


class User(TypedDict):
    is_staff: bool
    display_name: str


class APIOrganization(TypedDict):
    public_id: str
    name: str


class DashboardConfig(TypedDict):
    user: User
    organization: NotRequired[APIOrganization]
    """Organization data for dashboard access scoped to one organization. For staff members only."""

    routes: DashboardRoutes
