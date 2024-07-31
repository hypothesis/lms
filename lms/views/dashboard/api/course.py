from marshmallow import fields
from pyramid.view import view_config

from lms.js_config_types import APICourse, APICourses, CourseMetrics
from lms.models import Course
from lms.security import Permissions
from lms.services.h_api import HAPI
from lms.services.organization import OrganizationService
from lms.validation._base import PyramidRequestSchema
from lms.views.dashboard.pagination import PaginationParametersMixin, get_page


class ListCoursesSchema(PaginationParametersMixin):
    """Query parameters to fetch a list of courses."""

    h_userids = fields.List(fields.Str(), data_key="h_userid")
    """Return courses for these users only."""

    assignment_ids = fields.List(fields.Integer(), data_key="assignment_id")
    """Return only the courses to which these assigments belong."""

    public_id = fields.Str()
    """Return only the courses which belong to this organization. For staff member only."""


class CoursesMetricsSchema(PyramidRequestSchema):
    """Query parameters to fetch metrics for courses."""

    location = "querystring"

    h_userids = fields.List(fields.Str(), data_key="h_userid")
    """Return metrics for these users only."""

    assignment_ids = fields.List(fields.Integer(), data_key="assignment_id")
    """Return metrics for these assignments only."""

    course_ids = fields.List(fields.Integer(), data_key="course_id")
    """Return metrics for these courses only."""

    public_id = fields.Str()
    """Return only the courses which belong to this organization. For staff member only."""


class CourseViews:
    def __init__(self, request) -> None:
        self.request = request
        self.course_service = request.find_service(name="course")
        self.h_api = request.find_service(HAPI)
        self.organization_service = request.find_service(OrganizationService)
        self.dashboard_service = request.find_service(name="dashboard")
        self.assignment_service = request.find_service(name="assignment")

    @view_config(
        route_name="api.dashboard.courses",
        request_method="GET",
        renderer="json",
        permission=Permissions.DASHBOARD_VIEW,
        schema=ListCoursesSchema,
    )
    def courses(self) -> APICourses:
        filter_by_h_userids = self.request.parsed_params.get("h_userids")
        filter_by_assignment_ids = self.request.parsed_params.get("assignment_ids")
        admin_organizations = self.dashboard_service.get_request_admin_organizations(
            self.request
        )

        courses = self.course_service.get_courses(
            admin_organization_ids=[org.id for org in admin_organizations],
            instructor_h_userid=self.request.user.h_userid
            if self.request.user
            else None,
            h_userids=filter_by_h_userids,
            assignment_ids=filter_by_assignment_ids,
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
        route_name="api.dashboard.courses.metrics",
        request_method="GET",
        renderer="json",
        permission=Permissions.DASHBOARD_VIEW,
        schema=CoursesMetricsSchema,
    )
    def courses_metrics(self) -> APICourses:
        filter_by_h_userids = self.request.parsed_params.get("h_userids")
        filter_by_assignment_ids = self.request.parsed_params.get("assignment_ids")
        filter_by_course_ids = self.request.parsed_params.get("course_ids")
        admin_organizations = self.dashboard_service.get_request_admin_organizations(
            self.request
        )

        courses_query = self.course_service.get_courses(
            admin_organization_ids=[org.id for org in admin_organizations],
            instructor_h_userid=self.request.user.h_userid
            if self.request.user
            else None,
            h_userids=filter_by_h_userids,
            assignment_ids=filter_by_assignment_ids,
            course_ids=filter_by_course_ids,
        )
        courses = self.request.db.scalars(courses_query).all()

        courses_assignments_counts = (
            self.assignment_service.get_courses_assignments_count(
                admin_organization_ids=[org.id for org in admin_organizations],
                instructor_h_userid=self.request.user.h_userid
                if self.request.user
                else None,
                h_userids=filter_by_h_userids,
                assignment_ids=filter_by_assignment_ids,
                course_ids=[c.id for c in courses],
            )
        )

        return {
            "courses": [
                APICourse(
                    id=course.id,
                    title=course.lms_name,
                    course_metrics=CourseMetrics(
                        assignments=courses_assignments_counts.get(course.id, 0),
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
