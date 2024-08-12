from datetime import timedelta

from sqlalchemy import func, select, update

from lms.models import Course, CourseRoster, Event, LTIRole, User
from lms.models.h_user import get_h_userid, get_h_username

from lms.services.lti_names_roles import LTINamesRolesService, Member
from lms.services.lti_role_service import LTIRoleService
from lms.services.upsert import bulk_upsert

COURSE_LAUNCHED_WINDOW = timedelta(hours=24)
"""How recent we need to have seen a launch fro ma course before we stop fetching rosters."""

ROSTER_REFRESH_WINDOW = timedelta(hours=24 * 7)
"""How frequenly should we fetch roster for the same course"""


class CourseRosterService:
    def __init__(  # noqa: PLR0913
        self,
        db,
        lti_name_roles_service: LTINamesRolesService,
        application_instance_service,
        lti_role_service: LTIRoleService,
        h_authority: str,
    ):
        self._db = db
        self._lti_name_roles_service = lti_name_roles_service
        self._application_instance_service = application_instance_service
        self._lti_role_service = lti_role_service
        self._h_authority = h_authority

    def schedule_fetching_rosters(self):
        # Only fetch roster for courses that don't have recent roster information
        courses_with_recent_roster_subquery = (
            select(CourseRoster)
            .where(
                Course.authority_provided_id == CourseRoster.authority_provided_id,
                CourseRoster.updated >= func.now() - timedelta(hours=24),
            )
            .exists()
        )
        # Only fetch roster for courses that have been recently launched
        courses_with_recent_launch_subuqery = (
            select(Event)
            .where(
                Course.id == Event.course_id,
                Event.timestamp <= func.now() - timedelta(hours=24),
            )
            .exists()
        )

        query = (
            select(Course).where(
                ~courses_with_recent_roster_subquery,
                courses_with_recent_launch_subuqery,
                # Courses for which we have a LTIA membership service URL
                Course.lti_context_memberships_url.is_not(None),
            )
            # Schedule only a few roster per call to this method
            .limit(5)
        )

        for course in self._db.scalars(query).all():
            self.fetch_roster(
                course.lti_context_memberships_url,
                course.application_instance_id,
                course.authority_provided_id,
            )

    def fetch_roster(self, service_url, application_instance_id, authority_provided_id):
        ai = self._application_instance_service.get_by_id(application_instance_id)
        roster = self._lti_name_roles_service.get_context_memberships(
            ai.lti_registration, service_url
        )

        user_upsert_elements = []
        roster_upsert_elements = []
        for roster_user in roster:
            # Get the  roles from the DB
            roles = self._lti_role_service.get_roles(roster_user["roles"])
            # We might have found new roles, assign them a primary key flushing to the DB
            self._db.flush()

            # Get the h_userid for this user
            h_userid = get_h_userid(
                self._h_authority,
                get_h_username(ai.tool_consumer_instance_guid, roster_user["user_id"]),
            )

            # Prepare a row for each user we seen in the roster. We might already seen these via other luanches or roster requests
            user_upsert_elements.append(
                self._user_dict_from_member(
                    application_instance_id, h_userid, roster_user
                )
            )
            # We'll insert a roster row once per role
            for role in roles:
                roster_upsert_elements.append(
                    self._roster_dict_from_member(
                        authority_provided_id, h_userid, role, roster_user
                    )
                )

        # We'll first mark everyone as non-Active. We keep a record of how belonged to a course.
        self._db.execute(
            update(CourseRoster)
            .where(CourseRoster.authority_provided_id == authority_provided_id)
            .values(active=False)
        )

        # Insert any users we might have seen for the first time
        bulk_upsert(
            self._db,
            User,
            values=user_upsert_elements,
            index_elements=["user_id", "application_instance_id"],
            update_columns=["updated"],
        )
        # Insert and update roster rows.
        bulk_upsert(
            self._db,
            CourseRoster,
            values=roster_upsert_elements,
            index_elements=["authority_provided_id", "h_userid", "lti_role_id"],
            update_columns=["active", "updated"],
        )

    def _user_dict_from_member(
        self, application_instance_id, h_userid: str, member: Member
    ) -> dict:
        return {
            "application_instance_id": application_instance_id,
            "user_id": member.get("lti11_legacy_user_id") or member["user_id"],
            # We have more complex rules to build display names based on launch parameters. For now we'll just ervice and
            # we won't update the names fteched by this service
            # TODO USE COMMON FUNCTION
            "display_name": f'{member["name"]} {member["family_name"]}',
            "roles": ",".join(member["roles"]),
            "h_userid": h_userid,
        }

    def _roster_dict_from_member(
        self, authority_provided_id: str, h_userid: str, role: LTIRole, member: Member
    ) -> dict:
        return {
            "authority_provided_id": authority_provided_id,
            "h_userid": h_userid,
            "lti_role_id": role.id,
            "active": member["status"] == "Active",
        }

    @classmethod
    def factory(cls, _context, request):
        return CourseRosterService(
            db=request.db,
            lti_name_roles_service=request.find_service(LTINamesRolesService),
            application_instance_service=request.find_service(
                name="application_instance"
            ),
            lti_role_service=request.find_service(LTIRoleService),
            h_authority=request.registry.settings["h_authority"],
        )
