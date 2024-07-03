from pyramid.httpexceptions import HTTPNotFound, HTTPUnauthorized

from lms.security import Permissions
from lms.services.organization import OrganizationService


class DashboardService:
    def __init__(self, assignment_service, course_service, organization_service):
        self._assignment_service = assignment_service
        self._course_service = course_service
        self._organization_service = organization_service

    def get_request_assignment(self, request):
        """Get and authorize an assignment for the given request."""
        assigment_id = request.matchdict.get(
            "assignment_id"
        ) or request.parsed_params.get("assignment_id")
        assignment = self._assignment_service.get_by_id(assigment_id)
        if not assignment:
            raise HTTPNotFound()

        if request.has_permission(Permissions.STAFF):
            # STAFF members in our admin pages can access all assignments
            return assignment

        if not self._assignment_service.is_member(assignment, request.user.h_userid):
            raise HTTPUnauthorized()

        return assignment

    def get_request_course(self, request):
        """Get and authorize a course for the given request."""
        course = self._course_service.get_by_id(request.matchdict["course_id"])
        if not course:
            raise HTTPNotFound()

        if request.has_permission(Permissions.STAFF):
            # STAFF members in our admin pages can access all courses
            return course

        if not self._course_service.is_member(course, request.user.h_userid):
            raise HTTPUnauthorized()

        return course

    def get_request_organization(self, request):
        """Get and authorize an organization for the given request."""
        organization = self._organization_service.get_by_public_id(
            public_id=request.matchdict["organization_public_id"]
        )
        if not organization:
            raise HTTPNotFound()

        if request.has_permission(Permissions.STAFF):
            # STAFF members in our admin pages can access all organizations
            return organization

        if not self._organization_service.is_member(organization, request.user):
            raise HTTPUnauthorized()

        return organization


def factory(_context, request):
    return DashboardService(
        assignment_service=request.find_service(name="assignment"),
        course_service=request.find_service(name="course"),
        organization_service=request.find_service(OrganizationService),
    )
