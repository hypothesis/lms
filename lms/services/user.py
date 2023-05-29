from functools import lru_cache

from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.sql import Select

from lms.models import LTIUser, User


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

        user = User(
            application_instance_id=lti_user.application_instance.id,
            user_id=lti_user.user_id,
            roles=lti_user.roles,
            h_userid=lti_user.h_user.userid(self._h_authority),
        )

        if existing_user := self._db.execute(
            self._user_search_query(
                application_instance_id=user.application_instance_id,
                user_id=user.user_id,
            )
        ).scalar_one_or_none():
            # Update the existing user from the fields which can change on a
            # new one
            existing_user.roles = user.roles
            user = existing_user
        else:
            self._db.add(user)

        if lti_user.is_instructor:
            # We are only storing these personal details for teachers now.
            user.email = lti_user.email
            user.display_name = lti_user.display_name

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


def factory(_context, request):
    """Service factory for the UserService."""

    return UserService(request.db, request.registry.settings["h_authority"])
