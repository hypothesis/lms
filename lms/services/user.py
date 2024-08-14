from functools import lru_cache
from typing import cast

from sqlalchemy import BinaryExpression, false, or_, select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.sql import Select

from lms.models import (
    ApplicationInstance,
    Assignment,
    AssignmentMembership,
    LTIRole,
    LTIUser,
    RoleScope,
    RoleType,
    User,
)
from lms.services.course import CourseService


class UserNotFound(Exception):
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

    @lru_cache(maxsize=128)
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
            raise UserNotFound() from err

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

    def get_users(  # noqa: PLR0913, PLR0917
        self,
        role_scope: RoleScope,
        role_type: RoleType,
        instructor_h_userid: str | None = None,
        admin_organization_ids: list[int] | None = None,
        course_ids: list[int] | None = None,
        h_userids: list[str] | None = None,
        assignment_ids: list[int] | None = None,
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
        """
        query = select(User.id)

        # A few of the filters need to join with assignment_membership.
        # Avoid joins and/or multiple subqueries by building a subquery and filtering the main query
        # by it at the end
        assignment_membership_subquery = select(AssignmentMembership.user_id).where(
            AssignmentMembership.lti_role_id.in_(
                select(LTIRole.id).where(
                    LTIRole.scope == role_scope, LTIRole.type == role_type
                )
            )
        )

        # Let's crate no op clauses by default to avoid having to check the presence of these filters
        instructor_h_userid_clause = cast(BinaryExpression, false())
        admin_organization_ids_clause = cast(BinaryExpression, false())

        if instructor_h_userid:
            instructor_h_userid_clause = User.id.in_(
                select(AssignmentMembership.user_id)
                .join(Assignment)
                .where(
                    Assignment.course_id.in_(
                        CourseService.course_ids_with_role_query(
                            instructor_h_userid, RoleScope.COURSE, RoleType.INSTRUCTOR
                        )
                    )
                )
            )

        if admin_organization_ids:
            admin_organization_ids_clause = User.application_instance_id.in_(
                select(ApplicationInstance.id).where(
                    ApplicationInstance.organization_id.in_(admin_organization_ids)
                )
            )

        # instructor_h_userid and admin_organization_ids are about access rather than filtering.
        # we apply them both as an or to fetch users where the users is either an instructor or an admin
        query = query.where(
            or_(instructor_h_userid_clause, admin_organization_ids_clause)
        )

        if h_userids:
            query = query.where(User.h_userid.in_(h_userids))

        if course_ids:
            assignment_membership_subquery = assignment_membership_subquery.join(
                Assignment
            ).where(Assignment.course_id.in_(course_ids))

        if assignment_ids:
            assignment_membership_subquery = assignment_membership_subquery.where(
                AssignmentMembership.assignment_id.in_(assignment_ids)
            )

        query = query.where(User.id.in_(assignment_membership_subquery))

        # Deduplicate based on the row's h_userid taking the last updated one
        query = query.distinct(User.h_userid).order_by(
            User.h_userid, User.updated.desc()
        )

        return (
            select(User)
            .where(
                User.id.in_(query)
                # We can sort these again without affecting deduplication
            )
            .order_by(User.display_name, User.id)
        )


def factory(_context, request):
    """Service factory for the UserService."""

    return UserService(request.db, request.registry.settings["h_authority"])
