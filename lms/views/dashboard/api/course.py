from pyramid.view import view_config

from lms.js_config_types import (
    AnnotationMetrics,
    APIAssignment,
    APIAssignments,
    APICourse,
    APICourses,
    CourseMetrics,
)
from lms.models import Course, RoleScope, RoleType
from lms.security import Permissions
from lms.services.h_api import HAPI
from lms.services.organization import OrganizationService
from lms.views.dashboard.base import get_request_course, get_request_organization
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
        org = get_request_organization(self.request, self.organization_service)
        courses = self.course_service.get_courses(
            organization=org,
            h_userid=self.request.user.h_userid if self.request.user else None,
        )
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
        course = get_request_course(self.request, self.course_service)
        return {
            "id": course.id,
            "title": course.lms_name,
        }

    @view_config(
        route_name="api.dashboard.course.assignments.stats",
        request_method="GET",
        renderer="json",
        permission=Permissions.DASHBOARD_VIEW,
    )
    def course_assignments(self) -> APIAssignments:
        course = get_request_course(self.request, self.course_service)
        course_students = self.course_service.get_members(
            course, role_scope=RoleScope.COURSE, role_type=RoleType.LEARNER
        )

        stats = self.h_api.get_annotation_counts(
            # Annotations in the course group and any children
            [course.authority_provided_id]
            + [child.authority_provided_id for child in course.children],
            group_by="assignment",
            h_userids=[s.h_userid for s in course_students],
        )
        # Organize the H stats by assignment ID for quick access
        stats_by_assignment = {s["assignment_id"]: s for s in stats}
        assignments: list[APIAssignment] = []

        # Same course for all these assignments
        api_course = APICourse(id=course.id, title=course.lms_name)
        for assignment in self.course_service.get_assignments(
            course, h_userid=self.request.user.h_userid if self.request.user else None
        ):
            if h_stats := stats_by_assignment.get(assignment.resource_link_id):
                metrics = AnnotationMetrics(
                    annotations=h_stats["annotations"],
                    replies=h_stats["replies"],
                    last_activity=h_stats["last_activity"],
                )
            else:
                # Assignment with no annos, zeroing the stats
                metrics = AnnotationMetrics(
                    annotations=0, replies=0, last_activity=None
                )

            assignments.append(
                APIAssignment(
                    id=assignment.id,
                    title=assignment.title,
                    course=api_course,
                    annotation_metrics=metrics,
                )
            )

        return {"assignments": assignments}
