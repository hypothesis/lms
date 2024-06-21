import logging

from pyramid.view import view_config

from lms.js_config_types import (
    AnnotationMetrics,
    APIAssignment,
    APICourse,
    APIStudent,
    APIStudents,
)
from lms.models import RoleScope, RoleType
from lms.security import Permissions
from lms.services.h_api import HAPI
from lms.views.dashboard.base import get_request_assignment

LOG = logging.getLogger(__name__)


class AssignmentViews:
    def __init__(self, request) -> None:
        self.request = request
        self.h_api = request.find_service(HAPI)
        self.assignment_service = request.find_service(name="assignment")

    @view_config(
        route_name="api.dashboard.assignment",
        request_method="GET",
        renderer="json",
        permission=Permissions.DASHBOARD_VIEW,
    )
    def assignment(self) -> APIAssignment:
        assignment = get_request_assignment(self.request, self.assignment_service)
        return APIAssignment(
            id=assignment.id,
            title=assignment.title,
            course=APICourse(id=assignment.course.id, title=assignment.course.lms_name),
        )

    @view_config(
        route_name="api.dashboard.assignment.stats",
        request_method="GET",
        renderer="json",
        permission=Permissions.DASHBOARD_VIEW,
    )
    def assignment_stats(self) -> APIStudents:
        """Fetch the stats for one particular assignment."""
        assignment = get_request_assignment(self.request, self.assignment_service)
        LOG.debug(
            "Fetching stats from H for groups: %s and assignemnt %s",
            [g.authority_provided_id for g in assignment.groupings],
            assignment.resource_link_id,
        )
        stats = self.h_api.get_annotation_counts(
            [g.authority_provided_id for g in assignment.groupings],
            group_by="user",
            resource_link_id=assignment.resource_link_id,
        )
        LOG.debug("Recieved stats from H %s", stats)

        # Organize the H stats by userid for quick access
        stats_by_user = {s["userid"]: s for s in stats}
        students: list[APIStudent] = []

        # Iterate over all the students we have in the DB
        for user in self.assignment_service.get_members(
            assignment, role_scope=RoleScope.COURSE, role_type=RoleType.LEARNER
        ):
            if s := stats_by_user.get(user.h_userid):
                # We seen this student in H, get all the data from there
                students.append(
                    APIStudent(
                        id=user.user_id,
                        display_name=s["display_name"],
                        annotation_metrics=AnnotationMetrics(
                            annotations=s["annotations"],
                            replies=s["replies"],
                            last_activity=s["last_activity"],
                        ),
                    )
                )
            else:
                # We haven't seen this user H,
                # use LMS DB's data and set 0s for all annotation related fields.
                students.append(
                    APIStudent(
                        id=user.user_id,
                        display_name=user.display_name,
                        annotation_metrics=AnnotationMetrics(
                            annotations=0, replies=0, last_activity=None
                        ),
                    )
                )

        return {"students": students}
