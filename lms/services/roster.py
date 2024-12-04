from logging import getLogger

from sqlalchemy import Select, func, select, text, update

from lms.models import (
    ApplicationInstance,
    Assignment,
    AssignmentRoster,
    CourseRoster,
    LMSCourse,
    LMSCourseApplicationInstance,
    LMSSegment,
    LMSSegmentRoster,
    LMSUser,
    LTIRegistration,
    LTIRole,
    RoleScope,
    RoleType,
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

    def get_course_roster(
        self,
        lms_course: LMSCourse,
        role_scope: RoleScope | None = None,
        role_type: RoleType | None = None,
    ) -> Select[tuple[LMSUser]]:
        """Get the roster information for a course from our DB."""
        roster_query = (
            select(CourseRoster.lms_user_id)
            .join(LTIRole)
            .where(
                CourseRoster.lms_course_id == lms_course.id,
                CourseRoster.active.is_(True),
            )
        )

        if role_scope:
            roster_query = roster_query.where(LTIRole.scope == role_scope)

        if role_type:
            roster_query = roster_query.where(LTIRole.type == role_type)

        return select(LMSUser).where(LMSUser.id.in_(roster_query))

    def assignment_roster_exists(self, assignment: Assignment) -> bool:
        """Check if we have roster data for the given assignment."""
        return bool(
            self._db.scalar(
                select(AssignmentRoster)
                .where(AssignmentRoster.assignment_id == assignment.id)
                .limit(1)
            )
        )

    def get_assignment_roster(
        self,
        assignment: Assignment,
        role_scope: RoleScope | None = None,
        role_type: RoleType | None = None,
        h_userids: list[str] | None = None,
    ) -> Select[tuple[LMSUser]]:
        """Get the roster information for a course from our DB."""
        roster_query = (
            select(AssignmentRoster.lms_user_id)
            .join(LTIRole)
            .where(
                AssignmentRoster.assignment_id == assignment.id,
                AssignmentRoster.active.is_(True),
            )
        )

        if role_scope:
            roster_query = roster_query.where(LTIRole.scope == role_scope)

        if role_type:
            roster_query = roster_query.where(LTIRole.type == role_type)

        query = select(LMSUser).where(LMSUser.id.in_(roster_query))

        if h_userids:
            query = query.where(LMSUser.h_userid.in_(h_userids))

        return query

    def fetch_course_roster(self, lms_course: LMSCourse) -> None:
        """Fetch the roster information for a course from the LMS."""
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
        """Fetch the roster information for an assignment from the LMS."""
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
            if err.response_body and (
                # Canvas, unknown reason
                "Requested ResourceLink bound to unexpected external tool"
                in err.response_body
                # Canvas, assignment deleted in the LMS
                or "Requested ResourceLink was not found" in err.response_body
            ):
                LOG.error("Fetching assignment roster failed: %s", err.response_body)
                # We ignore this type of error, just stop here.
                return

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

    def fetch_canvas_group_roster(self, canvas_group: LMSSegment) -> None:
        """Fetch the roster information for an assignment from the LMS."""
        assert canvas_group.type == "canvas_group"

        lms_course = canvas_group.lms_course
        assert (
            lms_course.lti_context_memberships_url
        ), "Trying fetch roster for course without service URL."

        application_instance = self._db.scalars(
            select(ApplicationInstance)
            .join(LMSCourseApplicationInstance)
            .where(
                LMSCourseApplicationInstance.lms_course_id == lms_course.id,
                ApplicationInstance.lti_registration_id.is_not(None),
            )
            .order_by(ApplicationInstance.updated.desc())
        ).first()

        roster = self._lti_names_roles_service.get_context_memberships(
            application_instance.lti_registration,
            # We won't use the names and roles endpoint for groups, we need to pass a URL from the Canvas extension to the API.
            # https://canvas.instructure.com/doc/api/names_and_role.html#method.lti/ims/names_and_roles.group_index
            f"https://{application_instance.lms_host()}/api/lti/groups/{canvas_group.lms_id}/names_and_roles",
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
                        "lms_segment_id": canvas_group.id,
                        "lms_user_id": lms_users_by_lti_user_id[lti_user_id].id,
                        "lti_role_id": lti_roles_by_value[role].id,
                        "active": member["status"] == "Active",
                    }
                )
        # We'll first mark everyone as non-Active.
        # We keep a record of who belonged to a course even if they are no longer present.
        self._db.execute(
            update(LMSSegmentRoster)
            .where(LMSSegmentRoster.lms_segment_id == canvas_group.id)
            .values(active=False)
        )

        # Insert and update roster rows.
        bulk_upsert(
            self._db,
            LMSSegmentRoster,
            values=roster_upsert_elements,
            index_elements=["lms_segment_id", "lms_user_id", "lti_role_id"],
            update_columns=["active", "updated"],
        )

    def _get_roster_users(self, roster, tool_consumer_instance_guid):
        values = []
        for member in roster:
            lti_user_id = member.get("lti11_legacy_user_id") or member["user_id"]
            lti_v13_user_id = member["user_id"]
            lms_api_user_id = (
                member.get("message", [{}])[0]
                .get("https://purl.imsglobal.org/spec/lti/claim/custom", {})
                .get("canvas_user_id")
            )
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
                    "lti_v13_user_id": lti_v13_user_id,
                    "h_userid": h_userid,
                    "display_name": name,
                    "lms_api_user_id": lms_api_user_id,
                }
            )

        return bulk_upsert(
            self._db,
            LMSUser,
            values=values,
            index_elements=["h_userid"],
            update_columns=[
                "updated",
                # lti_v13_user_id is not going to change but we want to backfill it for existing users.
                "lti_v13_user_id",
                # Same for lms_api_user_id, not going to change for existing user but we are backfilling for now
                (
                    "lms_api_user_id",
                    func.coalesce(
                        text('"excluded"."lms_api_user_id"'),
                        text('"lms_user"."lms_api_user_id"'),
                    ),
                ),
            ],
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
