"""
Types of the config exposed to the frontend and API return values.

Making this a top level module to avoid circular dependency problems.
"""
from typing import NotRequired, TypedDict


class APICallInfo(TypedDict):
    path: str
    authUrl: NotRequired[str]


class APIAssignment(TypedDict):
    id: int
    title: str


class APIStudentStats(TypedDict):
    display_name: str
    annotations: int
    replies: int
    last_activity: str


class DashboardLinks(TypedDict):
    assignmentApi: str
    assignmentStatsApi: str


class DashboardConfig(TypedDict):
    links: DashboardLinks
