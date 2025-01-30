from datetime import datetime
from logging import getLogger

from sqlalchemy import Select, func, select, text, union, update

from lms.models import (
    ApplicationInstance,
    Assignment,
    AssignmentRoster,
    CourseRoster,
    Family,
    LMSCourse,
    LMSCourseApplicationInstance,
    LMSCourseMembership,
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
from lms.services.canvas_api.client import CanvasAPIClient
from lms.services.canvas_api.factory import canvas_api_client_factory
from lms.services.d2l_api.client import D2LAPIClient
from lms.services.exceptions import (
    CanvasAPIError,
    ConcurrentTokenRefreshError,
    ExternalRequestError,
    OAuth2TokenError,
)
from lms.services.lti_names_roles import LTINamesRolesService, Member
from lms.services.lti_role_service import LTIRoleService
from lms.services.oauth2_token import OAuth2TokenService
from lms.services.upsert import bulk_upsert

LOG = getLogger(__name__)


class RosterService:
    def __init__(
        self,
        request,
        lti_names_roles_service: LTINamesRolesService,
        lti_role_service: LTIRoleService,
        h_authority: str,
    ):
        self._request = request
        self._db = request.db
        self._lti_names_roles_service = lti_names_roles_service
        self._lti_role_service = lti_role_service
        self._h_authority = h_authority

    def assignment_roster_last_updated(self, assignment: Assignment) -> datetime | None:
        """Return the roster's last updated timestamp for given assignment, or None if we don't have roster data."""
        return self._db.scalar(
            select(AssignmentRoster.updated)
            .where(AssignmentRoster.assignment_id == assignment.id)
            .order_by(AssignmentRoster.updated.desc())
            .limit(1)
        )

    def segment_roster_last_updated(self, segment: LMSSegment) -> datetime | None:
        """Return the roster's last updated timestamp for a given segment, or None if we don't have roster data."""
        return self._db.scalar(
            select(LMSSegmentRoster.updated)
            .where(LMSSegmentRoster.lms_segment_id == segment.id)
            .order_by(LMSSegmentRoster.updated.desc())
            .limit(1)
        )

    def course_roster_last_updated(self, course: LMSCourse) -> datetime | None:
        """Return the roster's last updated timestamp for a given course, or None if we don't have roster data."""
        return self._db.scalar(
            select(CourseRoster.updated)
            .where(CourseRoster.lms_course_id == course.id)
            .order_by(CourseRoster.updated.desc())
            .limit(1)
        )

    def get_assignment_roster(
        self,
        assignment: Assignment,
        role_scope: RoleScope | None = None,
        role_type: RoleType | None = None,
        h_userids: list[str] | None = None,
    ) -> Select[tuple[LMSUser, bool]]:
        """Get the roster information for a course from our DB."""
        roster_query = (
            select(LMSUser, AssignmentRoster.active)
            .join(LMSUser, AssignmentRoster.lms_user_id == LMSUser.id)
            .join(LTIRole, AssignmentRoster.lti_role_id == LTIRole.id)
            .where(AssignmentRoster.assignment_id == assignment.id)
        ).distinct()

        return self._get_roster(roster_query, role_scope, role_type, h_userids)

    def get_segments_roster(
        self,
        segments: list[LMSSegment],
        role_scope: RoleScope | None = None,
        role_type: RoleType | None = None,
        h_userids: list[str] | None = None,
    ) -> Select[tuple[LMSUser, bool]]:
        """Get the roster information for a segment from our DB."""

        roster_query = (
            select(LMSUser, LMSSegmentRoster.active)
            .join(LMSUser, LMSSegmentRoster.lms_user_id == LMSUser.id)
            .join(LTIRole, LTIRole.id == LMSSegmentRoster.lti_role_id)
            .where(LMSSegmentRoster.lms_segment_id.in_([s.id for s in segments]))
        ).distinct()

        return self._get_roster(roster_query, role_scope, role_type, h_userids)

    def get_course_roster(
        self,
        lms_course: LMSCourse,
        role_scope: RoleScope | None = None,
        role_type: RoleType | None = None,
        h_userids: list[str] | None = None,
    ) -> Select[tuple[LMSUser, bool]]:
        """Get the roster information for a course from our DB."""
        roster_query = (
            select(LMSUser, CourseRoster.active)
            .join(LMSUser, CourseRoster.lms_user_id == LMSUser.id)
            .join(LTIRole, CourseRoster.lti_role_id == LTIRole.id)
            .where(CourseRoster.lms_course_id == lms_course.id)
        ).distinct()

        return self._get_roster(roster_query, role_scope, role_type, h_userids)

    def _get_roster(
        self,
        roster_query,
        role_scope: RoleScope | None = None,
        role_type: RoleType | None = None,
        h_userids: list[str] | None = None,
    ) -> Select[tuple[LMSUser, bool]]:
        """Filter a roster query by role and h_userids.

        Helper function for the get_*_roster methods.
        """
        if role_scope:
            roster_query = roster_query.where(LTIRole.scope == role_scope)

        if role_type:
            roster_query = roster_query.where(LTIRole.type == role_type)

        if h_userids:
            roster_query = roster_query.where(LMSUser.h_userid.in_(h_userids))

        return roster_query

    def fetch_course_roster(self, lms_course: LMSCourse) -> None:
        """Fetch the roster information for a course from the LMS."""
        assert lms_course.lti_context_memberships_url, (
            "Trying fetch roster for course without service URL."
        )
        application_instance = self._get_application_instance(lms_course)
        lti_registration = self._get_lti_registration(lms_course)

        roster = self._lti_names_roles_service.get_context_memberships(
            lti_registration, lms_course.lti_context_memberships_url
        )

        # Insert any users we might be missing in the DB
        lms_users_by_lti_user_id = {
            u.lti_user_id: u
            for u in self._get_roster_users(
                roster,
                application_instance.family,
                lms_course.tool_consumer_instance_guid,
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
        assert assignment.lti_v13_resource_link_id, (
            "Trying fetch roster for an assignment without LTI1.3 ID."
        )
        assert assignment.course, (
            "Trying fetch roster for an assignment without a course."
        )

        lms_course = self._db.scalars(
            select(LMSCourse).where(
                LMSCourse.h_authority_provided_id
                == assignment.course.authority_provided_id
            )
        ).one()

        assert lms_course.lti_context_memberships_url, (
            "Trying fetch roster for course without service URL."
        )
        application_instance = self._get_application_instance(lms_course)
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
                roster,
                application_instance.family,
                lms_course.tool_consumer_instance_guid,
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
        """Fetch the roster information for a canvas group from the LMS."""
        assert canvas_group.type == "canvas_group"

        lms_course = canvas_group.lms_course
        assert lms_course.lti_context_memberships_url, (
            "Trying fetch roster for course without service URL."
        )

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
                roster,
                application_instance.family,
                lms_course.tool_consumer_instance_guid,
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

    def fetch_canvas_sections_roster(self, lms_course: LMSCourse) -> None:
        """Fetch the roster information for all canvas sections for one particular course.

        Sections are different than other rosters:
             - We fetch them via the proprietary Canvas API, not the LTI Names and Roles endpoint.

             - Due to the return value of that API we don't fetch rosters for indivual sections,
               but for all sections of one course at once

             - The return value of the API doesn't include enough information to create unseen users
               so we'll only match against users we have seen before in the course.
        """
        application_instance = self._get_application_instance(lms_course)

        # Last instructor to launch the course, we'll use this user's API token to fetch the sections.
        instructor = self._get_course_instructor(lms_course)
        if not instructor:
            LOG.info(
                "Can't fetch roster for sections of course ID:%s. No instructor found.",
                lms_course.id,
            )
            return

        # Get all the sections for this course that we've seen in the DB.
        db_sections = self._db.scalars(
            select(LMSSegment).where(
                LMSSegment.lms_course_id == lms_course.id,
                LMSSegment.type == "canvas_section",
            )
        ).all()

        if not db_sections:
            LOG.info(
                "Can't fetch roster for sections of course ID:%s. No sections found in the DB.",
                lms_course.id,
            )
            return

        # We'll create a new Canvas API client for the relevant install and instructor to fetch the sections.
        canvas_service = canvas_api_client_factory(
            None,
            self._request,
            application_instance=application_instance,
            user_id=instructor.lti_user_id,
        )
        # We'll take the token service from the client to refresh the token if needed.
        # This is already scoped to the user and the install.
        oauth2_token_service = canvas_service._client._oauth2_token_service  # noqa: SLF001

        # Fetch the sections and their students from the Canvas API.
        api_sections = self._get_canvas_sections(
            canvas_service, oauth2_token_service, lms_course, with_refresh_token=True
        )
        if not api_sections:
            LOG.info(
                "Can't fetch roster for sections of course ID:%s. No sections found on the API.",
                lms_course.id,
            )
            return
        api_sections_by_id = {str(section["id"]): section for section in api_sections}

        # The API doesn't send a LTI role, we'll pick a student one from the DB and use that
        student_lti_role_id = self._db.scalar(
            select(LTIRole.id)
            .where(LTIRole.type == RoleType.LEARNER, LTIRole.scope == RoleScope.COURSE)
            .order_by(LTIRole.id.asc())
        )

        roster_upsert_elements = []
        db_course_users_by_lms_api_id = self._get_course_users(lms_course)
        for db_section in db_sections:
            api_section = api_sections_by_id.get(db_section.lms_id)
            if not api_section:
                LOG.debug(
                    "Skiping roster for section ID:%s. Not found on Canvas API",
                    db_section.lms_id,
                )
                continue

            for student in api_section.get("students", []) or []:
                db_student = db_course_users_by_lms_api_id.get(str(student["id"]))
                if not db_student:
                    LOG.debug(
                        "Skiping roster entry for student ID:%s. Not found the DB",
                        student["id"],
                    )
                    continue

                roster_upsert_elements.append(
                    {
                        "lms_segment_id": db_section.id,
                        "lms_user_id": db_student.id,
                        "lti_role_id": student_lti_role_id,
                        "active": True,
                    }
                )

        if not roster_upsert_elements:
            LOG.info(
                "No roster entries found for course ID:%s.",
                lms_course.id,
            )
            return

        # We'll first mark everyone as non-Active.
        # We keep a record of who belonged to a section even if they are no longer present.
        self._db.execute(
            update(LMSSegmentRoster)
            .where(LMSSegmentRoster.lms_segment_id.in_([s.id for s in db_sections]))
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

    def _get_roster_users(
        self, roster: list[Member], family: Family, tool_consumer_instance_guid
    ):
        values = []
        for member in roster:
            lti_user_id = member.get("lti11_legacy_user_id") or member["user_id"]
            lti_v13_user_id = member["user_id"]
            lms_api_user_id = self._get_lms_api_user_id(member, family)
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

    def _get_application_instance(self, lms_course) -> ApplicationInstance:
        return self._db.scalars(
            select(ApplicationInstance)
            .join(LMSCourseApplicationInstance)
            .where(LMSCourseApplicationInstance.lms_course_id == lms_course.id)
            .order_by(LMSCourseApplicationInstance.updated.desc())
        ).first()

    def _get_lti_registration(self, lms_course) -> LTIRegistration:
        ai = self._get_application_instance(lms_course)
        assert ai.lti_registration, "No LTI registration found for LMSCourse."
        return ai.lti_registration

    def _get_course_instructor(self, lms_course: LMSCourse) -> LMSUser | None:
        return self._db.scalars(
            select(LMSUser)
            .join(LMSCourseMembership)
            .join(LTIRole)
            .where(
                LMSCourseMembership.lms_course_id == lms_course.id,
                LTIRole.type == RoleType.INSTRUCTOR,
                LTIRole.scope == RoleScope.COURSE,
            )
            .order_by(LMSCourseMembership.updated.desc())
        ).first()

    def _get_canvas_sections(
        self,
        canvas_api_client: CanvasAPIClient,
        oauth2_token_service: OAuth2TokenService,
        lms_course: LMSCourse,
        with_refresh_token=False,
    ) -> list[dict]:
        try:
            return canvas_api_client.course_sections(
                lms_course.lms_api_course_id, with_students=True
            )
        except OAuth2TokenError as err:
            if not with_refresh_token or not err.refreshable:
                LOG.info(
                    "Failed to fetch sections for course %s, invalid API token",
                    lms_course.id,
                )
                return []

            if not self._refresh_canvas_token(canvas_api_client, oauth2_token_service):
                LOG.info(
                    "Failed to fetch sections for course %s, error refreshing token",
                    lms_course.id,
                )
                return []

            return self._get_canvas_sections(
                canvas_api_client,
                oauth2_token_service,
                lms_course,
                with_refresh_token=False,
            )

    def _refresh_canvas_token(
        self, canvas_service: CanvasAPIClient, oauth2_token_service
    ) -> bool:
        try:
            refresh_token = oauth2_token_service.get().refresh_token
            canvas_service.get_refreshed_token(refresh_token)
        except (ConcurrentTokenRefreshError, CanvasAPIError):
            return False

        return True

    def _get_course_users(self, lms_course: LMSCourse) -> dict[str, LMSUser]:
        users_from_course_roster = (
            select(LMSUser)
            .join(CourseRoster)
            .where(
                CourseRoster.lms_course_id == lms_course.id,
                CourseRoster.active.is_(True),
            )
        )
        users_from_launches = (
            select(LMSUser)
            .join(LMSCourseMembership)
            .where(
                LMSCourseMembership.lms_course_id == lms_course.id,
            )
        )
        users = self._db.execute(
            union(users_from_course_roster, users_from_launches)
        ).all()
        return {u.lms_api_user_id: u for u in users}

    def _get_lms_api_user_id(self, member: Member, family: Family) -> str | None:
        if family == Family.D2L:
            return D2LAPIClient.get_api_user_id(member["user_id"])

        return (
            member.get("message", [{}])[0]
            .get("https://purl.imsglobal.org/spec/lti/claim/custom", {})
            .get("canvas_user_id")
        )


def factory(_context, request):
    return RosterService(
        request=request,
        lti_names_roles_service=request.find_service(LTINamesRolesService),
        lti_role_service=request.find_service(LTIRoleService),
        h_authority=request.registry.settings["h_authority"],
    )
