from marshmallow import validate
from pyramid.httpexceptions import HTTPNotFound
from pyramid.view import view_config, view_defaults
from webargs import fields

from lms.models import Course
from lms.security import Permissions
from lms.validation._base import PyramidRequestSchema
from lms.views.admin import flash_validation
from lms.views.admin._schemas import EmptyStringInt


class SearchCourseSchema(PyramidRequestSchema):
    location = "form"

    # Max value for postgres `integer` type
    id = EmptyStringInt(required=False, validate=validate.Range(max=2147483647))
    name = fields.Str(required=False)
    context_id = fields.Str(required=False)


@view_defaults(request_method="GET", permission=Permissions.ADMIN)
class AdminOrganizationViews:
    def __init__(self, request) -> None:
        self.request = request
        self.course_service = request.find_service(name="course")
        self.assignment_service = request.find_service(name="assignment")

    @view_config(
        route_name="admin.course",
        request_method="GET",
        renderer="lms:templates/admin/course/show.html.jinja2",
        permission=Permissions.STAFF,
    )
    def show(self):
        course_id = self.request.matchdict["id_"]
        course = self._get_course_or_404(course_id)

        return {
            "course": course,
            "assignments": self.assignment_service.get_course_assignments(course),
        }

    """
    @view_config(
        route_name="admin.organizations",
        request_method="GET",
        renderer="lms:templates/admin/organization/search.html.jinja2",
        permission=Permissions.STAFF,
    )
    def organizations(self):  # pragma: no cover
        return {}

    @view_config(
        route_name="admin.course",
        request_method="GET",
        renderer="lms:templates/admin/organization/show.html.jinja2",
        permission=Permissions.STAFF,
    )
    @view_config(
        route_name="admin.organization.section",
        request_method="GET",
        renderer="lms:templates/admin/organization/show.html.jinja2",
        permission=Permissions.STAFF,
    )
    """

    @view_config(
        route_name="admin.courses",
        request_method="POST",
        renderer="lms:templates/admin/course/search.html.jinja2",
        permission=Permissions.STAFF,
    )
    def search(self):
        if flash_validation(self.request, SearchCourseSchema):
            return {}

        courses = self.course_service.search(
            id_=self.request.params.get("id", "").strip(),
            name=self.request.params.get("name", "").strip(),
            context_id=self.request.params.get("context_id", "").strip(),
        )

        return {"courses": courses}

    def _get_course_or_404(self, id_) -> Course:
        if course := self.course_service.search(id_=id_):
            return course[0]

        raise HTTPNotFound()
