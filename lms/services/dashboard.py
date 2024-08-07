from pyramid.httpexceptions import HTTPNotFound, HTTPUnauthorized
from sqlalchemy import select

from lms.models.dashboard_admin import DashboardAdmin
from lms.models.organization import Organization
from lms.security import Permissions
from lms.services.organization import OrganizationService


class DashboardService:
    def __init__(
        self,
        request,
        assignment_service,
        course_service,
        organization_service: OrganizationService,
    ):
        self._db = request.db

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

        admin_organizations = self.get_request_admin_organizations(request)
        if (
            admin_organizations
            and assignment.course.application_instance.organization
            in admin_organizations
        ):
            # Organization admins have access to all the assignments in their organizations
            return assignment

        # Access to the assignment is determined by access to its course.
        if not self._course_service.is_member(assignment.course, request.user.h_userid):
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

        admin_organizations = self.get_request_admin_organizations(request)
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
        organization_ids = []

        for org_id in self._db.scalars(
            select(DashboardAdmin.organization_id)
            .where(DashboardAdmin.email == email)
            .distinct()
        ).all():
            organization_ids.extend(
                self._organization_service.get_hierarchy_ids(org_id)
            )

        return self._db.scalars(
            select(Organization).where(Organization.id.in_(organization_ids))
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

    def get_request_admin_organizations(self, request) -> list[Organization]:
        """Get the organization the current user is an admin in."""
        if request.has_permission(Permissions.STAFF) and (
            request_public_id := request.params.get("public_id")
        ):
            # We handle permissions and filtering specially for staff members
            # If the request contains a filter for one organization, we will proceed as if the staff member
            # is an admin in that organization. That will provide access to its data and filter by it
            organization = self._organization_service.get_by_public_id(
                request_public_id
            )
            if not organization:
                raise HTTPNotFound()

            return self._db.scalars(
                select(Organization).where(
                    Organization.id.in_(
                        self._organization_service.get_hierarchy_ids(organization.id)
                    )
                )
            ).all()

        return self.get_organizations_by_admin_email(
            request.lti_user.email if request.lti_user else request.identity.userid
        )


def factory(_context, request):
    return DashboardService(
        request=request,
        assignment_service=request.find_service(name="assignment"),
        course_service=request.find_service(name="course"),
        organization_service=request.find_service(OrganizationService),
    )
