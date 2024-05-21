"""
Types of the config exposed to the frontend and API return values.

Making this a top level module to avoid circular dependency problems.
"""

from typing import NotRequired, TypeAlias, TypedDict

URLTemplate: TypeAlias = str
"""Templates are string that containt templated URL with parameter names like:

    /course/:course_id/
    /course/:course_id/assignment/:assignment
"""


class APICallInfo(TypedDict):
    path: str
    authUrl: NotRequired[str]


class APICourse(TypedDict):
    id: int
    title: str


class APIStudentStats(TypedDict):
    display_name: str
    annotations: int
    replies: int
    last_activity: str | None


class AssignmentStats(TypedDict):
    annotations: int
    replies: int
    last_activity: str | None


class APIAssignment(TypedDict):
    id: int
    title: str
    course: APICourse
    stats: NotRequired[AssignmentStats]


class DashboardLinks(TypedDict):
    """Expose the URL of different top level dashboards."""

    assignment: URLTemplate
    course: URLTemplate


class DashboardRoutes(TypedDict):
    """Expose routes of the available API endpoints."""

    assignment: URLTemplate
    assignment_stats: URLTemplate

    course: URLTemplate
    course_assignment_stats: URLTemplate


class DashboardConfig(TypedDict):
    routes: DashboardRoutes
    links: DashboardLinks
