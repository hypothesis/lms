from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config

from lms.security import Permissions
from lms.services.h_api import HAPI


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
        assignment_id = self.request.matchdict["id_"]
        return HTTPFound(
            location=self.request.route_url("dashboard.assignment", id_=assignment_id),
        )

    @view_config(
        route_name="dashboard.assignment",
        permission=Permissions.DASHBOARD_VIEW,
        request_method="GET",
    )
    def assignment_show(self):
        assignment = self.assignment_service.get_by_id(self.request.matchdict["id_"])
        self.request.context.js_config.enable_dashboard_mode(assignment)
        return {}

    @view_config(
        route_name="api.assignment.stats",
        request_method="GET",
        renderer="json",
        permission=Permissions.DASHBOARD_VIEW,
    )
    def api_assignment_analytics(self):  # pragma: nocover
        return {}
