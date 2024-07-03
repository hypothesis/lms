from pyramid.view import view_config

from lms.js_config_types import APICourse, APICourses, CourseMetrics
from lms.models import Course
from lms.security import Permissions
from lms.services.h_api import HAPI
from lms.services.organization import OrganizationService
from lms.views.dashboard.pagination import PaginationParametersMixin, get_page

MAX_ITEMS_PER_PAGE = 100
"""Maximum number of items to return in paginated endpoints"""


class ListCoursesSchema(PaginationParametersMixin):
    """Query parameters to fetch a list of courses.

    Only the pagination related ones from the mixin.
    """


class CourseViews:
    def __init__(self, request) -> None:
        self.request = request
        self.course_service = request.find_service(name="course")
        self.h_api = request.find_service(HAPI)
        self.organization_service = request.find_service(OrganizationService)
        self.dashboard_service = request.find_service(name="dashboard")

    @view_config(
        route_name="api.dashboard.courses",
        request_method="GET",
        renderer="json",
        permission=Permissions.DASHBOARD_VIEW,
        schema=ListCoursesSchema,
    )
    def courses(self) -> APICourses:
        courses = self.course_service.get_courses(
            h_userid=self.request.user.h_userid if self.request.user else None,
        )
        courses, pagination = get_page(
            self.request, courses, [Course.lms_name, Course.id]
        )
        return {
            "courses": [
                APICourse(id=course.id, title=course.lms_name) for course in courses
            ],
            "pagination": pagination,
        }

    @view_config(
        route_name="api.dashboard.organizations.courses",
        request_method="GET",
        renderer="json",
        permission=Permissions.DASHBOARD_VIEW,
    )
    def organization_courses(self) -> APICourses:
        org = self.dashboard_service.get_request_organization(self.request)
        courses = self.request.db.scalars(
            self.course_service.get_courses(
                organization=org,
                h_userid=self.request.user.h_userid if self.request.user else None,
            )
        ).all()
        courses_assignment_counts = self.course_service.get_courses_assignments_count(
            courses
        )

        return {
            "courses": [
                APICourse(
                    id=course.id,
                    title=course.lms_name,
                    course_metrics=CourseMetrics(
                        assignments=courses_assignment_counts.get(course.id, 0),
                        last_launched=course.updated.isoformat(),
                    ),
                )
                for course in courses
            ]
        }

    @view_config(
        route_name="api.dashboard.course",
        request_method="GET",
        renderer="json",
        permission=Permissions.DASHBOARD_VIEW,
    )
    def course(self) -> APICourse:
        course = self.dashboard_service.get_request_course(self.request)
        return {
            "id": course.id,
            "title": course.lms_name,
        }
