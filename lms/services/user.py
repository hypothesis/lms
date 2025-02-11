from functools import lru_cache

from sqlalchemy import exists, func, select, text
from sqlalchemy.exc import NoResultFound
from sqlalchemy.sql import Select

from lms.models import (
    AssignmentMembership,
    Family,
    Grouping,
    LMSCourse,
    LMSCourseMembership,
    LMSSegmentMembership,
    LMSUser,
    LMSUserApplicationInstance,
    LMSUserAssignmentMembership,
    LTIParams,
    LTIRole,
    LTIUser,
    RoleScope,
    RoleType,
    User,
)
from lms.models.lms_segment import LMSSegment
from lms.services.course import CourseService
from lms.services.lti_names_roles import Member
from lms.services.upsert import bulk_upsert


class UserNotFound(Exception):  # noqa: N818
    """The requested User wasn't found in the database."""


class UserService:
    """
    A service for working with users.

    At the moment this is purely used for recording/reporting purposes.
    """

    def __init__(self, db, h_authority: str):
        self._db = db
        self._h_authority = h_authority

    def upsert_user(self, lti_user: LTIUser) -> User:
        """Store a record of having seen a particular user."""

        # Note! - Storing a user in our DB currently has an implication for
        # reporting and so billing and will as long as our billing metric is
        # tied to users in groups. Should we start to store users who have not
        # launched us, we could inflate our numbers or change their meaning.

        user = self._db.execute(
            self._user_search_query(
                application_instance_id=lti_user.application_instance_id,
                user_id=lti_user.user_id,
            )
        ).scalar_one_or_none()

        if not user:
            user = User(
                application_instance_id=lti_user.application_instance_id,
                user_id=lti_user.user_id,
                roles=lti_user.roles,
                h_userid=lti_user.h_user.userid(self._h_authority),
            )
            self._db.add(user)

        user.roles = lti_user.roles
        user.display_name = lti_user.display_name
        if lti_user.is_instructor:
            # We are only storing emails for teachers now.
            user.email = lti_user.email

        return user

    def upsert_lms_user(self, user: User, lti_params: LTIParams) -> LMSUser:
        """Upsert LMSUser based on a User object."""
        self._db.flush()  # Make sure User has hit the DB on the current transaction

        lms_api_user_id = self.get_lms_api_user_id(
            lti_params, user.application_instance.family
        )
        lms_user = bulk_upsert(
            self._db,
            LMSUser,
            [
                {
                    "tool_consumer_instance_guid": user.application_instance.tool_consumer_instance_guid,
                    "lti_user_id": user.user_id,
                    "lti_v13_user_id": lti_params.v13.get("sub"),
                    "h_userid": user.h_userid,
                    "email": user.email,
                    "display_name": user.display_name,
                    "lms_api_user_id": lms_api_user_id,
                }
            ],
            index_elements=["h_userid"],
            update_columns=[
                "updated",
                "display_name",
                "email",
                (
                    "lti_v13_user_id",
                    func.coalesce(
                        text('"excluded"."lti_v13_user_id"'),
                        text('"lms_user"."lti_v13_user_id"'),
                    ),
                ),
                (
                    "lms_api_user_id",
                    func.coalesce(
                        text('"excluded"."lms_api_user_id"'),
                        text('"lms_user"."lms_api_user_id"'),
                    ),
                ),
            ],
        ).one()
        bulk_upsert(
            self._db,
            LMSUserApplicationInstance,
            [
                {
                    "application_instance_id": user.application_instance_id,
                    "lms_user_id": lms_user.id,
                }
            ],
            index_elements=["application_instance_id", "lms_user_id"],
            update_columns=["updated"],
        )
        return lms_user

    @lru_cache(maxsize=128)  # noqa: B019
    def get(self, application_instance, user_id: str) -> User:
        """
        Get a User that belongs to `application_instance` with the given id.

        :param application_instance: The ApplicationInstance the user belongs to
        :param user_id: Unique identifier of the user
        :raises UserNotFound: if the User is not present in the DB
        """

        try:
            existing_user = self._db.execute(
                self._user_search_query(
                    application_instance_id=application_instance.id, user_id=user_id
                )
            ).scalar_one()

        except NoResultFound as err:
            raise UserNotFound from err

        return existing_user

    def _user_search_query(self, application_instance_id, user_id) -> Select:
        """Generate a query for searching for users."""

        query = select(User)

        # Normally we'd have an `if application_instance_id` here, for a proper
        # search query builder, but at the moment all arguments are mandatory,
        # and doing that would give us a coverage gap.
        query = query.where(User.application_instance_id == application_instance_id)

        # Ditto `if user_id`
        query = query.where(User.user_id == user_id)

        return query

    def get_users_for_assignment(
        self,
        role_scope: RoleScope,
        role_type: RoleType,
        assignment_id: int,
        h_userids: list[str] | None = None,
    ) -> Select[tuple[LMSUser]]:
        """Get the users that belong to one assignment."""
        query = (
            select(LMSUser)
            .distinct()
            .join(
                LMSUserAssignmentMembership,
                LMSUserAssignmentMembership.lms_user_id == LMSUser.id,
            )
            .where(
                LMSUserAssignmentMembership.assignment_id == assignment_id,
                LMSUserAssignmentMembership.lti_role_id.in_(
                    select(LTIRole.id).where(
                        LTIRole.scope == role_scope, LTIRole.type == role_type
                    )
                ),
            )
        )
        if h_userids:
            query = query.where(LMSUser.h_userid.in_(h_userids))

        return query

    def get_users_for_course(
        self,
        role_scope: RoleScope,
        role_type: RoleType,
        course_id: int,
        h_userids: list[str] | None = None,
    ) -> Select[tuple[LMSUser]]:
        """Get the users that belong to one course."""
        query = (
            select(LMSUser)
            .distinct()
            .join(
                LMSCourseMembership,
                LMSCourseMembership.lms_user_id == LMSUser.id,
            )
            .join(LMSCourse, LMSCourse.id == LMSCourseMembership.lms_course_id)
            # course_id is the PK on Grouping, we need to join with LMSCourse by authority_provided_id
            .join(
                Grouping,
                Grouping.authority_provided_id == LMSCourse.h_authority_provided_id,
            )
            .where(
                Grouping.id == course_id,
                LMSCourseMembership.lti_role_id.in_(
                    select(LTIRole.id).where(
                        LTIRole.scope == role_scope, LTIRole.type == role_type
                    )
                ),
            )
        )
        if h_userids:
            query = query.where(LMSUser.h_userid.in_(h_userids))

        return query.order_by(LMSUser.display_name, LMSUser.id)

    def get_users_for_segments(
        self,
        role_scope: RoleScope,
        role_type: RoleType,
        segment_ids: list[int],
        h_userids: list[str] | None = None,
    ) -> Select[tuple[LMSUser]]:
        """Get the users that belong to a list of segment.

        This method doesn't use roste data, just launches.
        """
        query = (
            select(LMSUser)
            .distinct()
            .join(
                LMSSegmentMembership,
                LMSSegmentMembership.lms_user_id == LMSUser.id,
            )
            .where(
                LMSSegmentMembership.lms_segment_id.in_(segment_ids),
                LMSSegmentMembership.lti_role_id.in_(
                    select(LTIRole.id).where(
                        LTIRole.scope == role_scope, LTIRole.type == role_type
                    )
                ),
            )
        )
        if h_userids:
            query = query.where(LMSUser.h_userid.in_(h_userids))

        return query.order_by(LMSUser.display_name, LMSUser.id)

    def get_users_for_organization(  # noqa: PLR0913
        self,
        role_scope: RoleScope,
        role_type: RoleType,
        course_ids: list[int] | None = None,
        instructor_h_userid: str | None = None,
        admin_organization_ids: list[int] | None = None,
        h_userids: list[str] | None = None,
    ) -> Select[tuple[LMSUser]]:
        candidate_courses = CourseService.courses_permission_check_query(
            instructor_h_userid, admin_organization_ids, course_ids=course_ids
        ).cte("candidate_courses")

        query = (
            select(LMSUser)
            .distinct()
            .join(LMSCourseMembership, LMSCourseMembership.lms_user_id == LMSUser.id)
            .join(LMSCourse, LMSCourseMembership.lms_course_id == LMSCourse.id)
            .join(
                Grouping,
                Grouping.authority_provided_id == LMSCourse.h_authority_provided_id,
            )
            .join(candidate_courses, candidate_courses.c[0] == Grouping.id)
            .where(
                LMSCourseMembership.lti_role_id.in_(
                    select(LTIRole.id).where(
                        LTIRole.scope == role_scope, LTIRole.type == role_type
                    )
                )
            )
        )

        if h_userids:
            query = query.where(LMSUser.h_userid.in_(h_userids))

        return query.order_by(LMSUser.display_name, LMSUser.id)

    def get_users(  # noqa: PLR0913
        self,
        role_scope: RoleScope,
        role_type: RoleType,
        instructor_h_userid: str | None = None,
        admin_organization_ids: list[int] | None = None,
        course_ids: list[int] | None = None,
        h_userids: list[str] | None = None,
        assignment_ids: list[int] | None = None,
        segment_authority_provided_ids: list[str] | None = None,
    ) -> Select[tuple[LMSUser]]:
        """
        Get a query to fetch users.

        :param role_scope: return only users with this LTI role scope.
        :param role_type: return only users with this LTI role type.
        :param instructor_h_userid: return only users that belong to courses where the user instructor_h_userid is an instructor.
        :param admin_organization_ids: organizations where the current user is an admin.
        :param h_userids: return only users with a h_userid in this list.
        :param course_ids: return only users that belong to these courses.
        :param assignment_ids: return only users that belong these assignments.
        :param segment_authority_provided_ids: return only users that belong these segments.
        """
        query = self.get_users_for_organization(
            role_scope=role_scope,
            role_type=role_type,
            instructor_h_userid=instructor_h_userid,
            admin_organization_ids=admin_organization_ids,
            h_userids=h_userids,
            course_ids=course_ids,
        )

        if assignment_ids:
            query = query.where(
                exists(
                    select(AssignmentMembership)
                    .join(User)
                    .where(
                        User.h_userid == LMSUser.h_userid,
                        AssignmentMembership.assignment_id.in_(assignment_ids),
                    )
                )
            )

        if segment_authority_provided_ids:
            query = query.where(
                exists(
                    select(LMSSegmentMembership)
                    .join(LMSSegment)
                    .where(
                        LMSSegmentMembership.lms_user_id == LMSUser.id,
                        LMSSegment.h_authority_provided_id.in_(
                            segment_authority_provided_ids
                        ),
                    )
                )
            )

        return query.order_by(LMSUser.display_name, LMSUser.id)

    @staticmethod
    def get_lms_api_user_id(data: Member | LTIParams, family: Family) -> str | None:
        """Get the API user id based off a launch or a roster member.

        In some LMS the LTI id and the ID of the same user on the proprietary API are different.
        """
        if family == Family.D2L:
            from lms.services.d2l_api.client import D2LAPIClient

            return D2LAPIClient.get_api_user_id(data["user_id"])

        if isinstance(data, LTIParams):
            return data.get("custom_canvas_user_id")

        return (
            data.get("message", [{}])[0]
            .get("https://purl.imsglobal.org/spec/lti/claim/custom", {})
            .get("canvas_user_id")
        )


def factory(_context, request):
    """Service factory for the UserService."""

    return UserService(request.db, request.registry.settings["h_authority"])
