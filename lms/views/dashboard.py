from pyramid.httpexceptions import HTTPFound, HTTPNotFound, HTTPUnauthorized
from pyramid.view import view_config

from lms.models import RoleScope, RoleType
from lms.security import Permissions
from lms.services.h_api import HAPI
from lms.validation.authentication import BearerTokenSchema


class DashboardViews:
    def __init__(self, request) -> None:
        self.request = request
        self.h_api = request.find_service(HAPI)
        self.assignment_service = request.find_service(name="assignment")

    @view_config(
        route_name="dashboard.launch.assignment",
        permission=Permissions.DASHBOARD_VIEW,
        request_method="POST",
    )
    def assignment_redirect_from_launch(self):
        """
        Entry point to the dashboards from an LTI launch.

        Here we "promote" the LTILaunch token present as a form parameter to a cookie.
        """
        assignment_id = self.request.matchdict["id_"]
        response = HTTPFound(
            location=self.request.route_url("dashboard.assignment", id_=assignment_id),
        )
        self._set_lti_user_cookie(response)
        return response

    @view_config(
        route_name="dashboard.assignment",
        permission=Permissions.DASHBOARD_VIEW,
        request_method="GET",
        renderer="lms:templates/dashboard.html.jinja2",
    )
    def assignment_show(self):
        """Start the dashboard miniapp in the frontend.

        Authenticated via the LTIUser present in a cookie making this endpoint accessible directly in the browser.
        """
        assignment = self.get_request_assignment()
        self.request.context.js_config.enable_dashboard_mode(assignment)
        self._set_lti_user_cookie(self.request.response)
        return {}

    @view_config(
        route_name="api.assignment.stats",
        request_method="GET",
        renderer="json",
        permission=Permissions.DASHBOARD_VIEW,
    )
    def api_assignment_stats(self):
        """Fetch the stats for one particular assignment."""
        assignment = self.get_request_assignment()
        stats = self.h_api.get_assignment_stats(
            [g.authority_provided_id for g in assignment.groupings],
            assignment.resource_link_id,
        )

        # Organize the H stats by userid for quick access
        stats_by_user = {s["userid"]: s for s in stats}
        student_stats = []

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
                        "replies": 0,
                        "last_activity": None,
                    }
                )

        return student_stats

    def get_request_assignment(self):
        assignment = self.assignment_service.get_by_id(self.request.matchdict["id_"])
        if not assignment:
            raise HTTPNotFound()

        if self.request.has_permission(Permissions.STAFF):
            # STAFF members in our admin pages can access all assignments
            return assignment

        if not self.assignment_service.is_member(assignment, self.request.user):
            raise HTTPUnauthorized()

        return assignment

    def _set_lti_user_cookie(self, response):
        auth_token = (
            BearerTokenSchema(self.request).authorization_param(self.request.lti_user)
            # White space is not allowed as a cookie character, remove the leading part
            .replace("Bearer ", "")
        )
        response.set_cookie(
            "authorization",
            value=auth_token,
            secure=not self.request.registry.settings["dev"],
            httponly=True,
            max_age=60 * 60 * 24,  # 24 hours, matches the lifetime of the auth_token
        )
        return response
