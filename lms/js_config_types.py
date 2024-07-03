"""
Types of the config exposed to the frontend and API return values.

Making this a top level module to avoid circular dependency problems.
"""

from typing import NotRequired, TypedDict


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


class APICourses(TypedDict):
    courses: list[APICourse]

    pagination: NotRequired[Pagination]


class APIAssignment(TypedDict):
    id: int
    title: str
    course: NotRequired[APICourse]
    annotation_metrics: NotRequired[AnnotationMetrics]


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

    organization_courses: str

    courses: str
    """Paginated endpoint to fetch courses"""
    assignments: str
    """Paginated endpoint to fetch assigments"""
    students: str
    """Paginated endpoint to fetch students"""


class User(TypedDict):
    is_staff: bool
    display_name: str


class DashboardConfig(TypedDict):
    user: User
    routes: DashboardRoutes
