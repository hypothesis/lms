from pyramid.view import view_config

from lms.js_config_types import APIAssignment, APIStudentStats
from lms.models import RoleScope, RoleType
from lms.security import Permissions
from lms.services.h_api import HAPI
from lms.views.dashboard.base import get_request_assignment


class AssignmentViews:
    def __init__(self, request) -> None:
        self.request = request
        self.h_api = request.find_service(HAPI)
        self.assignment_service = request.find_service(name="assignment")

    @view_config(
        route_name="dashboard.api.assignment",
        request_method="GET",
        renderer="json",
        permission=Permissions.DASHBOARD_VIEW,
    )
    def assignment(self) -> APIAssignment:
        assignment = get_request_assignment(self.request, self.assignment_service)
        return {
            "id": assignment.id,
            "title": assignment.title,
        }

    @view_config(
        route_name="dashboard.api.assignment.stats",
        request_method="GET",
        renderer="json",
        permission=Permissions.DASHBOARD_VIEW,
    )
    def assignment_stats(self) -> list[APIStudentStats]:
        """Fetch the stats for one particular assignment."""
        assignment = get_request_assignment(self.request, self.assignment_service)
        stats = self.h_api.get_assignment_stats(
            [g.authority_provided_id for g in assignment.groupings],
            assignment.resource_link_id,
        )

        # Organize the H stats by userid for quick access
        stats_by_user = {s["userid"]: s for s in stats}
        student_stats: list[APIStudentStats] = []

        # Iterate over all the students we have in the DB
        for user in self.assignment_service.get_members(
            assignment, role_scope=RoleScope.COURSE, role_type=RoleType.LEARNER
        ):
            if s := stats_by_user.get(user.h_userid):
                # We seen this student in H, get all the data from there
                student_stats.append(
                    {
                        "display_name": s["display_name"],
                        "annotations": s["annotations"],
                        "replies": s["replies"],
                        "last_activity": s["last_activity"],
                    }
                )
            else:
                # We haven't seen this user H,
                # use LMS DB's data and set 0s for all annotation related fields.
                student_stats.append(
                    {
                        "display_name": user.display_name
                        or f"Student {user.user_id[:10]}",
                        "annotations": 0,
                        "last_activity": None,
                        "replies": 0,
                    }
                )

        return student_stats
