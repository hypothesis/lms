from datetime import timedelta

from pyramid.httpexceptions import HTTPFound
from pyramid.view import forbidden_view_config, view_config

from lms.security import Permissions
from lms.services import OrganizationService
from lms.validation.authentication import BearerTokenSchema

AUTHORIZATION_DURATION_SECONDS = 60 * 60 * 24 * 7  # One week


@forbidden_view_config(
    route_name="dashboard.launch.assignment",
    request_method="POST",
    renderer="lms:templates/dashboard/forbidden.html.jinja2",
)
@forbidden_view_config(
    route_name="dashboard.assignment",
    request_method="GET",
    renderer="lms:templates/dashboard/forbidden.html.jinja2",
)
@forbidden_view_config(
    route_name="dashboard.course",
    request_method="GET",
    renderer="lms:templates/dashboard/forbidden.html.jinja2",
)
@forbidden_view_config(
    route_name="dashboard",
    request_method="GET",
    renderer="lms:templates/dashboard/forbidden.html.jinja2",
)
def forbidden(_request):  # pragma: no cover
    return {}


class DashboardViews:
    def __init__(self, request) -> None:
        self.request = request
        self.assignment_service = request.find_service(name="assignment")
        self.course_service = request.find_service(name="course")
        self.organization_service: OrganizationService = request.find_service(
            OrganizationService
        )
        self.dashboard_service = request.find_service(name="dashboard")

    @view_config(
        route_name="dashboard.launch.assignment",
        permission=Permissions.DASHBOARD_VIEW,
        request_method="POST",
    )
    def assignment_redirect_from_launch(self):
        """
        Entry point to the single assignment view from an LTI launch.

        Here we "promote" the LTILaunch token present as a form parameter to a cookie.
        """
        assignment_id = self.request.matchdict["assignment_id"]
        response = HTTPFound(
            location=self.request.route_url(
                "dashboard.assignment", assignment_id=assignment_id
            ),
        )
        self._set_lti_user_cookie(response)
        return response

    @view_config(
        route_name="dashboard.assignment",
        permission=Permissions.DASHBOARD_VIEW,
        request_method="GET",
        renderer="lms:templates/dashboard/index.html.jinja2",
    )
    @view_config(
        route_name="dashboard.organization.assignment",
        permission=Permissions.DASHBOARD_VIEW,
        request_method="GET",
        renderer="lms:templates/dashboard/index.html.jinja2",
    )
    def assignment_show(self):
        """Start the dashboard miniapp in the frontend.

        Authenticated via the LTIUser present in a cookie making this endpoint accessible directly in the browser.
        """
        assignment = self.dashboard_service.get_request_assignment(
            self.request, self.request.matchdict["assignment_id"]
        )
        self.request.context.js_config.enable_dashboard_mode(
            AUTHORIZATION_DURATION_SECONDS
        )
        self._set_lti_user_cookie(self.request.response)
        return {"title": assignment.title}

    @view_config(
        route_name="dashboard.course",
        permission=Permissions.DASHBOARD_VIEW,
        request_method="GET",
        renderer="lms:templates/dashboard/index.html.jinja2",
    )
    @view_config(
        route_name="dashboard.organization.course",
        permission=Permissions.DASHBOARD_VIEW,
        request_method="GET",
        renderer="lms:templates/dashboard/index.html.jinja2",
    )
    def course_show(self):
        """Start the dashboard miniapp in the frontend.

        Authenticated via the LTIUser present in a cookie making this endpoint accessible directly in the browser.
        """
        course = self.dashboard_service.get_request_course(
            self.request, self.request.matchdict["course_id"]
        )
        self.request.context.js_config.enable_dashboard_mode(
            AUTHORIZATION_DURATION_SECONDS
        )
        self._set_lti_user_cookie(self.request.response)
        return {"title": course.lms_name}

    @view_config(
        route_name="dashboard",
        permission=Permissions.DASHBOARD_VIEW,
        request_method="GET",
        renderer="lms:templates/dashboard/index.html.jinja2",
    )
    @view_config(
        route_name="dashboard.organization",
        permission=Permissions.DASHBOARD_VIEW,
        request_method="GET",
        renderer="lms:templates/dashboard/index.html.jinja2",
    )
    def courses(self):
        """Start the dashboard miniapp in the frontend scoped to an organization.

        Authenticated via the LTIUser present in a cookie making this endpoint accessible directly in the browser.
        """
        self.request.context.js_config.enable_dashboard_mode(
            AUTHORIZATION_DURATION_SECONDS
        )
        self._set_lti_user_cookie(self.request.response)
        # Org names are not 100% ready for public consumption, let's hardcode a title for now.
        return {"title": "All courses"}

    def _set_lti_user_cookie(self, response):
        lti_user = self.request.lti_user
        if not lti_user:
            # An LTIUser might not exist if accessing from the admin pages.
            return response
        auth_token = (
            BearerTokenSchema(self.request)
            .authorization_param(
                lti_user, lifetime=timedelta(seconds=AUTHORIZATION_DURATION_SECONDS)
            )
            # White space is not allowed as a cookie character, remove the leading part
            .replace("Bearer ", "")
        )
        response.set_cookie(
            "authorization",
            value=auth_token,
            secure=not self.request.registry.settings["dev"],
            httponly=True,
            # Scope the cookie to all dashboard views
            path="/dashboard",
            max_age=AUTHORIZATION_DURATION_SECONDS,
        )
        return response
