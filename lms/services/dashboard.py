from datetime import datetime

from pyramid.httpexceptions import HTTPNotFound, HTTPUnauthorized
from sqlalchemy import Select, select, union

from lms.models import (
    ApplicationInstance,
    Assignment,
    LMSCourse,
    LMSCourseApplicationInstance,
    LMSCourseMembership,
    LMSUser,
    LTIRole,
    Organization,
    RoleScope,
    RoleType,
)
from lms.models.dashboard_admin import DashboardAdmin
from lms.security import Permissions
from lms.services import OrganizationService, RosterService, UserService


class DashboardService:
    def __init__(  # noqa: PLR0913, PLR0917
        self,
        request,
        assignment_service,
        course_service,
        roster_service: RosterService,
        organization_service: OrganizationService,
        user_service: UserService,
        h_authority: str,
    ):
        self._db = request.db

        self._assignment_service = assignment_service
        self._course_service = course_service
        self._roster_service = roster_service
        self._user_service = user_service
        self._organization_service = organization_service
        self._h_authority = h_authority

    def get_request_assignment(self, request, assigment_id: int) -> Assignment:
        """Get and authorize an assignment for the given request."""
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

    def get_request_course(self, request, course_id: int):
        """Get and authorize a course for the given request."""
        course = self._course_service.get_by_id(course_id)
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

    def get_organizations_where_admin(
        self, h_userid: str, email: str
    ) -> list[Organization]:
        """Get a list of organizations where the user h_userid with email `email` is an admin in."""
        organization_ids = []

        # A user can be an admin in an organization via having a matching email in DashboardAdmin
        organization_id_by_email = select(DashboardAdmin.organization_id).where(
            DashboardAdmin.email == email
        )

        # It also can be an admin via having the relevant LTI role in an organization.
        organization_id_by_lti_admin = (
            select(Organization.id)
            .join(
                ApplicationInstance,
                ApplicationInstance.organization_id == Organization.id,
            )
            .join(
                LMSCourseApplicationInstance,
                LMSCourseApplicationInstance.application_instance_id
                == ApplicationInstance.id,
            )
            .join(LMSCourse, LMSCourse.id == LMSCourseApplicationInstance.lms_course_id)
            .join(
                LMSCourseMembership, LMSCourseMembership.lms_course_id == LMSCourse.id
            )
            .join(LMSUser, LMSCourseMembership.lms_user_id == LMSUser.id)
            .join(LTIRole)
            .where(
                LMSUser.h_userid == h_userid,
                LTIRole.type == RoleType.ADMIN,
                LTIRole.scope == RoleScope.SYSTEM,
            )
        )

        for org_id in self._db.scalars(
            union(organization_id_by_email, organization_id_by_lti_admin)
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
            request_public_id := request.params.get("org_public_id")
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

        return self.get_organizations_where_admin(
            h_userid=request.lti_user.h_user.userid(self._h_authority),
            email=request.lti_user.email
            if request.lti_user
            else request.identity.userid,
        )

    def get_assignment_roster(
        self, assignment: Assignment, h_userids: list[str] | None = None
    ) -> tuple[datetime | None, Select[tuple[LMSUser, bool]]]:
        rosters_enabled = (
            assignment.course
            and assignment.course.application_instance.settings.get(
                "dashboard", "rosters"
            )
        )
        roster_last_updated = self._roster_service.assignment_roster_last_updated(
            assignment
        )

        if rosters_enabled and roster_last_updated:
            # If rostering is enabled and we do have the data, use it
            query = self._roster_service.get_assignment_roster(
                assignment,
                role_scope=RoleScope.COURSE,
                role_type=RoleType.LEARNER,
                h_userids=h_userids,
            )

        else:
            # If we are not going to return data from the roster, don't return the last updated date
            roster_last_updated = None
            # Always fallback to fetch users that have launched the assignment at some point
            query = self._user_service.get_users_for_assignment(
                role_scope=RoleScope.COURSE,
                role_type=RoleType.LEARNER,
                assignment_id=assignment.id,
                h_userids=h_userids,
                # For launch data we always add the "active" column as true for compatibility with the roster query.
            ).add_columns(True)

        # Always return the results, no matter the source, sorted
        return roster_last_updated, query.order_by(LMSUser.display_name, LMSUser.id)


def factory(_context, request):
    return DashboardService(
        request=request,
        assignment_service=request.find_service(name="assignment"),
        course_service=request.find_service(name="course"),
        organization_service=request.find_service(OrganizationService),
        roster_service=request.find_service(RosterService),
        user_service=request.find_service(UserService),
        h_authority=request.registry.settings["h_authority"],
    )
