from pyramid.httpexceptions import HTTPNotFound, HTTPUnauthorized
from sqlalchemy import select

from lms.models.dashboard_admin import DashboardAdmin
from lms.models.organization import Organization
from lms.security import Permissions
from lms.services.organization import OrganizationService


class DashboardService:
    def __init__(self, db, assignment_service, course_service, organization_service):
        self._db = db

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

    def get_request_organizations(self, request) -> list[Organization]:
        """Get the relevant organizations for the current requests."""
        organizations = []

        # If we have an user, include the organization it belongs to
        if request.lti_user:
            lti_user_organization = request.lti_user.application_instance.organization

            if not self._organization_service.is_member(
                lti_user_organization, request.user
            ):
                raise HTTPUnauthorized()

            organizations.append(lti_user_organization)

        # Include any other organizations we are an admin in
        admin_organizations = self.get_organizations_by_admin_email(
            request.lti_user.email if request.lti_user else request.identity.userid
        )
        organizations.extend(admin_organizations)

        if not organizations:
            raise HTTPUnauthorized()

        return organizations

    def get_organizations_by_admin_email(self, email: str) -> list[Organization]:
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
        db=request.db,
        assignment_service=request.find_service(name="assignment"),
        course_service=request.find_service(name="course"),
        organization_service=request.find_service(OrganizationService),
    )
