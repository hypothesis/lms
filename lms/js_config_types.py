"""
Types of the config exposed to the frontend and API return values.

Making this a top level module to avoid circular dependency problems.
"""

from typing import NotRequired, TypedDict


class AnnotationMetrics(TypedDict):
    annotations: int
    replies: int
    last_activity: str | None


class APICallInfo(TypedDict):
    path: str
    authUrl: NotRequired[str]


class APICourse(TypedDict):
    id: int
    title: str


class APIStudent(TypedDict):
    id: str
    display_name: str | None

    annotation_metrics: NotRequired[AnnotationMetrics]


class APICourses(TypedDict):
    courses: list[APICourse]


class APIAssignment(TypedDict):
    id: int
    title: str
    course: APICourse
    annotation_metrics: NotRequired[AnnotationMetrics]


class APIAssignments(TypedDict):
    assignments: list[APIAssignment]


class APIStudents(TypedDict):
    students: list[APIStudent]


class DashboardRoutes(TypedDict):
    assignment: str
    assignment_stats: str

    course: str
    course_assignment_stats: str


class DashboardConfig(TypedDict):
    routes: DashboardRoutes
