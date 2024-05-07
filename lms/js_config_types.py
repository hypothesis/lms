from typing import NotRequired, TypedDict


class APICallInfo(TypedDict):
    path: str
    authUrl: NotRequired[str]


class AssignmentConfig(TypedDict):
    title: str


class AssignmentDashboardConfig(TypedDict):
    assignment: AssignmentConfig

    assignmentStatsApi: APICallInfo
