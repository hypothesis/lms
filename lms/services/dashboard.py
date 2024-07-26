from pyramid.httpexceptions import HTTPNotFound, HTTPUnauthorized
from sqlalchemy import select

from lms.models.dashboard_admin import DashboardAdmin
from lms.models.organization import Organization
from lms.security import Permissions
from lms.services.organization import OrganizationService


class DashboardService:
    def __init__(
        self, request, assignment_service, course_service, organization_service
    ):
        self._db = request.db

        self._assignment_service = assignment_service
        self._course_service = course_service
        self._organization_service = organization_service

    def get_request_assignment(self, request, admin_organizations: list[Organization]):
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

        if (
            admin_organizations
            and assignment.course.application_instance.organization
            in admin_organizations
        ):
            # Organization admins have access to all the assignments in their organizations
            return assignment

        if not self._assignment_service.is_member(assignment, request.user.h_userid):
            raise HTTPUnauthorized()

        return assignment

    def get_request_course(self, request, admin_organizations: list[Organization]):
        """Get and authorize a course for the given request."""
        course = self._course_service.get_by_id(request.matchdict["course_id"])
        if not course:
            raise HTTPNotFound()

        if request.has_permission(Permissions.STAFF):
            # STAFF members in our admin pages can access all courses
            return course

        if (
            admin_organizations
            and course.application_instance.organization in admin_organizations
        ):
            # Organization admins have access to all the courses in their organizations
            return course

        if not self._course_service.is_member(course, request.user.h_userid):
            raise HTTPUnauthorized()

        return course

    def get_organizations_by_admin_email(self, email: str) -> list[Organization]:
        """Get a list of organizations where the user with email `email` is an admin in."""
        return self._db.scalars(
            select(Organization)
            .join(DashboardAdmin)
            .where(DashboardAdmin.email == email)
            .distinct()
        ).all()

    def add_dashboard_admin(
        self, organization: Organization, email: str, created_by: str
    ) -> DashboardAdmin:
        """Create a new dashboard admin for `organization`."""
        admin = DashboardAdmin(
            organization=organization, created_by=created_by, email=email
        )
        self._db.add(admin)
        return admin

    def delete_dashboard_admin(self, dashboard_admin_id: int) -> None:
        """Delete an existing dashboard admin."""
        self._db.query(DashboardAdmin).filter_by(id=dashboard_admin_id).delete()


def factory(_context, request):
    return DashboardService(
        request=request,
        assignment_service=request.find_service(name="assignment"),
        course_service=request.find_service(name="course"),
        organization_service=request.find_service(OrganizationService),
    )
