from functools import lru_cache

from sqlalchemy import func, select, text
from sqlalchemy.exc import NoResultFound
from sqlalchemy.sql import Select

from lms.models import (
    Assignment,
    AssignmentMembership,
    Grouping,
    GroupingMembership,
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
from lms.services.course import CourseService
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

        # API ID, only Canvas for now
        lms_api_user_id = lti_params.get("custom_canvas_user_id")
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
                "lms_api_user_id",
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

    def get_users_for_organization(
        self,
        role_scope: RoleScope,
        role_type: RoleType,
        instructor_h_userid: str | None = None,
        admin_organization_ids: list[int] | None = None,
        h_userids: list[str] | None = None,
    ) -> Select[tuple[LMSUser]]:
        candidate_courses = CourseService.courses_permission_check_query(
            instructor_h_userid, admin_organization_ids, course_ids=None
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
    ) -> Select[tuple[User]]:
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

        candidate_courses = CourseService.courses_permission_check_query(
            instructor_h_userid, admin_organization_ids, course_ids
        ).cte("candidate_courses")

        user_ids_query = (
            select(AssignmentMembership.user_id)
            .join(Assignment)
            .join(candidate_courses, candidate_courses.c[0] == Assignment.course_id)
            .where(
                AssignmentMembership.lti_role_id.in_(
                    select(LTIRole.id).where(
                        LTIRole.scope == role_scope, LTIRole.type == role_type
                    )
                )
            )
        )

        if assignment_ids:
            user_ids_query = user_ids_query.where(
                AssignmentMembership.assignment_id.in_(assignment_ids)
            )

        if segment_authority_provided_ids:
            user_ids_query = user_ids_query.where(
                AssignmentMembership.user_id.in_(
                    select(GroupingMembership.user_id)
                    .join(Grouping)
                    .where(
                        Grouping.authority_provided_id.in_(
                            segment_authority_provided_ids
                        )
                    )
                )
            )

        query = (
            select(User.id)
            .distinct(User.h_userid)
            # Deduplicate based on the row's h_userid taking the last updated one
            .where(User.id.in_(user_ids_query))
            .order_by(User.h_userid, User.updated.desc())
        )

        if h_userids:
            query = query.where(User.h_userid.in_(h_userids))

        return (
            select(User)
            .where(User.id.in_(query))
            # We can sort these again without affecting deduplication
            .order_by(User.display_name, User.id)
        )


def factory(_context, request):
    """Service factory for the UserService."""

    return UserService(request.db, request.registry.settings["h_authority"])
