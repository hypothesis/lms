from pyramid.httpexceptions import HTTPNotFound
from pyramid.view import view_config, view_defaults
from lms.models import RoleScope, RoleType
from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from lms.validation.authentication import BearerTokenSchema
from lms.services.lti_user import LTIUserService

from lms.models import Assignment
from lms.security import Permissions


@view_defaults(request_method="GET", permission=Permissions.ADMIN)
class AdminAssignmentViews:
    def __init__(self, request) -> None:
        self.request = request
        self.assignment_service = request.find_service(name="assignment")
        self._lti_user_service = request.find_service(iface=LTIUserService)

    @view_config(
        route_name="admin.assignment",
        request_method="GET",
        renderer="lms:templates/admin/assignment/show.html.jinja2",
        permission=Permissions.STAFF,
    )
    def show(self):
        assignment_id = self.request.matchdict["id_"]
        assignment = self._get_or_404(assignment_id)

        return {
            "assignment": assignment,
        }

    @view_config(
        route_name="admin.assignment.dashboard",
        request_method="GET",
        permission=Permissions.STAFF,
    )
    def assignment_dashboard(self):
        assignment_id = self.request.matchdict["id_"]
        assignment = self._get_or_404(assignment_id)

        # Find instructors for the assigment
        members = self.assignment_service.get_members(
            assignment, role_scope=RoleScope.COURSE, role_type=RoleType.INSTRUCTOR
        )
        if not members:
            raise ValueError()

        lti_user = self._lti_user_service.impersonate(self.request, members[0])
        response = HTTPFound(
            location=self.request.route_url("dashboard.assignment", id_=assignment_id),
        )
        auth_token = (
            BearerTokenSchema(self.request).authorization_param(lti_user)
            # White space is not allowed as a cookie character, remove the leading part
            .replace("Bearer ", "")
        )
        response.set_cookie(
            "authorization",
            value=auth_token,
            secure=not self.request.registry.settings["dev"],
            httponly=True,
            max_age=60 * 60 * 24,
        )
        return response

    def _get_or_404(self, id_) -> Assignment:
        if assignment := self.assignment_service.get_by_id(id_=id_):
            return assignment

        raise HTTPNotFound()
