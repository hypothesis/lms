import json

from marshmallow import ValidationError, fields, post_load
from pyramid.view import view_config
from sqlalchemy.orm import Query

from lms.js_config_types import (
    AnnotationMetrics,
    APIAssignment,
    APIAssignments,
    APICourse,
    APICourses,
    CourseMetrics,
    Pagination,
)
from lms.models import Course, RoleScope, RoleType
from lms.security import Permissions
from lms.services.h_api import HAPI
from lms.services.organization import OrganizationService
from lms.validation._base import PyramidRequestSchema
from lms.views.dashboard.base import get_request_course, get_request_organization

MAX_ITEMS_PER_PAGE = 100
"""Maximum number of items to return in paginated endpoints"""


def get_courses_page(
    request, courses_query: Query[Course], limit: int = MAX_ITEMS_PER_PAGE
) -> tuple[list[Course], Pagination]:
    """Return the first page and pagination metadata from a courses query."""
    # Over fetch one element to check if need to calculate the next cursor
    courses = courses_query.limit(limit + 1).all()
    if not courses or len(courses) <= limit:
        return courses, Pagination(next=None)

    courses = courses[0:limit]
    last_element = courses[-1]
    cursor_data = json.dumps([last_element.lms_name, last_element.id])
    next_url_query = {"cursor": cursor_data}
    # Include query parameters in the original request so clients can use the next param verbatim.
    if limit := request.params.get("limit"):
        next_url_query["limit"] = limit

    return courses, Pagination(
        next=request.route_url("api.dashboard.courses", _query=next_url_query)
    )


class ListCoursesSchema(PyramidRequestSchema):
    location = "query"

    limit = fields.Integer(required=False, load_default=MAX_ITEMS_PER_PAGE)
    """Maximum number of items to return."""

    cursor = fields.Str()
    """Position to return elements from."""

    @post_load
    def decode_cursor(self, in_data, **_kwargs):
        cursor = in_data.get("cursor")
        if not cursor:
            return in_data

        try:
            in_data["cursor"] = json.loads(cursor)
        except ValueError as exc:
            raise ValidationError("Invalid value for pagination cursor.") from exc

        return in_data


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

        limit = min(MAX_ITEMS_PER_PAGE, self.request.parsed_params["limit"])
        if cursor_values := self.request.parsed_params.get("cursor"):
            cursor_course_name, cursor_course_id = cursor_values
            courses = courses.filter(
                (Course.lms_name, Course.id) > (cursor_course_name, cursor_course_id)
            )
        courses, pagination = get_courses_page(self.request, courses, limit)
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
