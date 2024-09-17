"""
Types of the config exposed to the frontend and API return values.

Making this a top level module to avoid circular dependency problems.
"""

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
    last_activity: str | None


class CourseMetrics(TypedDict):
    assignments: int
    last_launched: str | None


class APICallInfo(TypedDict):
    path: str
    authUrl: NotRequired[str]


class APICourse(TypedDict):
    id: int
    title: str

    course_metrics: NotRequired[CourseMetrics]


class APIStudent(TypedDict):
    h_userid: str
    """ID of the student in H."""

    lms_id: str
    """ID of the student in the LMS."""

    display_name: str | None

    annotation_metrics: NotRequired[AnnotationMetrics]

    auto_grading_grade: NotRequired[float]


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
    course: NotRequired[APICourse]

    sections: NotRequired[list[APISegment]]
    groups: NotRequired[list[APISegment]]

    annotation_metrics: NotRequired[AnnotationMetrics]
    auto_grading_config: NotRequired[AutoGradingConfig]


class APIAssignments(TypedDict):
    assignments: list[APIAssignment]

    pagination: NotRequired[Pagination]


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


class DashboardConfig(TypedDict):
    user: User
    routes: DashboardRoutes

    auto_grading_sync_enabled: bool
    """Whether or nor the opotion to sync grades back to the LMS is enabled."""
