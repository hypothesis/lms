"""
Types of the config exposed to the frontend and API return values.

Making this a top level module to avoid circular dependency problems.
"""

from typing import NotRequired, TypedDict


class APICallInfo(TypedDict):
    path: str
    authUrl: NotRequired[str]


class APICourse(TypedDict):
    id: int
    title: str


class APICourses(TypedDict):
    courses: list[APICourse]


class APIStudentStats(TypedDict):
    display_name: str
    annotations: int
    replies: int
    last_activity: str | None


class APIStudents(TypedDict):
    students: list[APIStudentStats]


class AssignmentStats(TypedDict):
    annotations: int
    replies: int
    last_activity: str | None


class APIAssignment(TypedDict):
    id: int
    title: str
    course: APICourse
    stats: NotRequired[AssignmentStats]


class APIAssignments(TypedDict):
    assignments: list[APIAssignment]


class DashboardRoutes(TypedDict):
    assignment: str
    assignment_stats: str

    course: str
    course_assignment_stats: str


class DashboardConfig(TypedDict):
    routes: DashboardRoutes
