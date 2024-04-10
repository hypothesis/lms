from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config

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
        # Encode the current LTIUser as a cookie
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
        assignment = self.assignment_service.get_by_id(self.request.matchdict["id_"])
        self.request.context.js_config.enable_dashboard_mode(assignment)
        return {}

    @view_config(
        route_name="api.assignment.stats",
        request_method="GET",
        renderer="json",
        permission=Permissions.DASHBOARD_VIEW,
    )
    def api_assignment_stats(self):
        """Fetch the stats for one particular assignment."""
        assignment = self.assignment_service.get_by_id(self.request.matchdict["id_"])
        stats = self.h_api.get_assignment_stats(
            [g.authority_provided_id for g in assignment.groupings],
            assignment.resource_link_id,
        )
        return [
            {
                "display_name": s["display_name"],
                "annotations": s["annotations"],
                "last_activity": s["last_activity"],
                "replies": s["replies"],
            }
            for s in stats
        ]
