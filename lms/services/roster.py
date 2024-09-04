from logging import getLogger

from sqlalchemy import select, update

from lms.models import (
    ApplicationInstance,
    Assignment,
    AssignmentRoster,
    CourseRoster,
    LMSCourse,
    LMSCourseApplicationInstance,
    LMSUser,
    LTIRegistration,
    LTIRole,
)
from lms.models.h_user import get_h_userid, get_h_username
from lms.models.lti_user import display_name
from lms.services.exceptions import ExternalRequestError
from lms.services.lti_names_roles import LTINamesRolesService
from lms.services.lti_role_service import LTIRoleService
from lms.services.upsert import bulk_upsert

LOG = getLogger(__name__)


class RosterService:
    def __init__(
        self,
        db,
        lti_names_roles_service: LTINamesRolesService,
        lti_role_service: LTIRoleService,
        h_authority: str,
    ):
        self._db = db
        self._lti_names_roles_service = lti_names_roles_service
        self._lti_role_service = lti_role_service
        self._h_authority = h_authority

    def fetch_course_roster(self, lms_course: LMSCourse) -> None:
        assert (
            lms_course.lti_context_memberships_url
        ), "Trying fetch roster for course without service URL."
        lti_registration = self._get_lti_registration(lms_course)

        roster = self._lti_names_roles_service.get_context_memberships(
            lti_registration, lms_course.lti_context_memberships_url
        )

        # Insert any users we might be missing in the DB
        lms_users_by_lti_user_id = {
            u.lti_user_id: u
            for u in self._get_roster_users(
                roster, lms_course.tool_consumer_instance_guid
            )
        }
        # Also insert any roles we might be missing
        lti_roles_by_value: dict[str, LTIRole] = {
            r.value: r for r in self._get_roster_roles(roster)
        }

        # Make sure any new rows have IDs
        self._db.flush()

        roster_upsert_elements = []

        for member in roster:
            lti_user_id = member.get("lti11_legacy_user_id") or member["user_id"]
            # Now, for every user + role, insert a row  in the roster table
            for role in member["roles"]:
                roster_upsert_elements.append(
                    {
                        "lms_course_id": lms_course.id,
                        "lms_user_id": lms_users_by_lti_user_id[lti_user_id].id,
                        "lti_role_id": lti_roles_by_value[role].id,
                        "active": member["status"] == "Active",
                    }
                )
        # We'll first mark everyone as non-Active.
        # We keep a record of who belonged to a course even if they are no longer present.
        self._db.execute(
            update(CourseRoster)
            .where(CourseRoster.lms_course_id == lms_course.id)
            .values(active=False)
        )

        # Insert and update roster rows.
        bulk_upsert(
            self._db,
            CourseRoster,
            values=roster_upsert_elements,
            index_elements=["lms_course_id", "lms_user_id", "lti_role_id"],
            update_columns=["active", "updated"],
        )

    def fetch_assignment_roster(self, assignment: Assignment) -> None:
        assert (
            assignment.lti_v13_resource_link_id
        ), "Trying fetch roster for an assignment without LTI1.3 ID."
        assert (
            assignment.course
        ), "Trying fetch roster for an assignment without a course."

        lms_course = self._db.scalars(
            select(LMSCourse).where(
                LMSCourse.h_authority_provided_id
                == assignment.course.authority_provided_id
            )
        ).one()

        assert (
            lms_course.lti_context_memberships_url
        ), "Trying fetch roster for course without service URL."
        lti_registration = self._get_lti_registration(lms_course)

        try:
            roster = self._lti_names_roles_service.get_context_memberships(
                lti_registration,
                lms_course.lti_context_memberships_url,
                resource_link_id=assignment.lti_v13_resource_link_id,
            )
        except ExternalRequestError as err:
            if (
                err.response_body
                and (
                    # Error message from Canvas
                    "Requested ResourceLink bound to unexpected external tool"
                    in err.response_body
                )
                # In cases for which we have different assignment IDs
                and assignment.resource_link_id != assignment.lti_v13_resource_link_id
            ):
                # The LMS (Canvas) doesn't seem to be able to link our tool to this assignment
                # Try the same call but with the LTI1.1 assignment identifier.
                LOG.info("Try to fetch roster with the LTI1.1 identifier")
                roster = self._lti_names_roles_service.get_context_memberships(
                    lti_registration,
                    lms_course.lti_context_memberships_url,
                    resource_link_id=assignment.resource_link_id,
                )
            else:
                raise

        # Insert any users we might be missing in the DB
        lms_users_by_lti_user_id = {
            u.lti_user_id: u
            for u in self._get_roster_users(
                roster, lms_course.tool_consumer_instance_guid
            )
        }
        # Also insert any roles we might be missing
        lti_roles_by_value: dict[str, LTIRole] = {
            r.value: r for r in self._get_roster_roles(roster)
        }

        # Make sure any new rows have IDs
        self._db.flush()

        roster_upsert_elements = []

        for member in roster:
            lti_user_id = member.get("lti11_legacy_user_id") or member["user_id"]
            # Now, for every user + role, insert a row  in the roster table
            for role in member["roles"]:
                roster_upsert_elements.append(
                    {
                        "assignment_id": assignment.id,
                        "lms_user_id": lms_users_by_lti_user_id[lti_user_id].id,
                        "lti_role_id": lti_roles_by_value[role].id,
                        "active": member["status"] == "Active",
                    }
                )
        # We'll first mark everyone as non-Active.
        # We keep a record of who belonged to a course even if they are no longer present.
        self._db.execute(
            update(AssignmentRoster)
            .where(AssignmentRoster.assignment_id == assignment.id)
            .values(active=False)
        )

        # Insert and update roster rows.
        bulk_upsert(
            self._db,
            AssignmentRoster,
            values=roster_upsert_elements,
            index_elements=["assignment_id", "lms_user_id", "lti_role_id"],
            update_columns=["active", "updated"],
        )

    def _get_roster_users(self, roster, tool_consumer_instance_guid):
        values = []
        for member in roster:
            lti_user_id = member.get("lti11_legacy_user_id") or member["user_id"]
            name = display_name(
                given_name=member.get("name", ""),
                family_name=member.get("family_name", ""),
                full_name="",
                custom_display_name="",
            )

            h_userid = get_h_userid(
                self._h_authority,
                get_h_username(tool_consumer_instance_guid, lti_user_id),
            )

            values.append(
                {
                    "tool_consumer_instance_guid": tool_consumer_instance_guid,
                    "lti_user_id": lti_user_id,
                    "h_userid": h_userid,
                    "display_name": name,
                }
            )

        return bulk_upsert(
            self._db,
            LMSUser,
            values=values,
            index_elements=["h_userid"],
            update_columns=["updated"],
        )

    def _get_roster_roles(self, roster) -> list[LTIRole]:
        roles = {role for member in roster for role in member["roles"]}
        return self._lti_role_service.get_roles(list(roles))

    def _get_lti_registration(self, lms_course) -> LTIRegistration:
        lti_registration = self._db.scalars(
            select(LTIRegistration)
            .join(ApplicationInstance)
            .where(LMSCourseApplicationInstance.lms_course_id == lms_course.id)
            .join(LMSCourseApplicationInstance)
            .order_by(LTIRegistration.updated.desc())
        ).first()
        assert lti_registration, "No LTI registration found for LMSCourse."
        return lti_registration


def factory(_context, request):
    return RosterService(
        db=request.db,
        lti_names_roles_service=request.find_service(LTINamesRolesService),
        lti_role_service=request.find_service(LTIRoleService),
        h_authority=request.registry.settings["h_authority"],
    )
