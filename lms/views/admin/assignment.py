from pyramid.httpexceptions import HTTPNotFound
from pyramid.view import view_config, view_defaults

from lms.models import Assignment
from lms.security import Permissions


@view_defaults(request_method="GET", permission=Permissions.ADMIN)
class AdminAssignmentViews:
    def __init__(self, request) -> None:
        self.request = request
        self.assignment_service = request.find_service(name="assignment")

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

    def _get_or_404(self, id_) -> Assignment:
        if assignment := self.assignment_service.get_by_id(id_=id_):
            return assignment

        raise HTTPNotFound()
