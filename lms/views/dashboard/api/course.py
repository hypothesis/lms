from pyramid.view import view_config

from lms.js_config_types import APICourse
from lms.security import Permissions
from lms.views.dashboard.base import get_request_course


class CourseViews:
    def __init__(self, request) -> None:
        self.request = request
        self.course_service = request.find_service(name="course")

    @view_config(
        route_name="dashboard.api.course",
        request_method="GET",
        renderer="json",
        permission=Permissions.DASHBOARD_VIEW,
    )
    def course(self) -> APICourse:
        course = get_request_course(self.request, self.course_service)
        return {
            "id": course.id,
            "title": course.lms_name,
        }
