from functools import lru_cache
from typing import Optional

from sqlalchemy.exc import NoResultFound

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
            application_instance_id=lti_user.application_instance_id,
            user_id=lti_user.user_id,
            roles=lti_user.roles,
            h_userid=lti_user.h_user.userid(self._h_authority),
        )

        if existing_user := self._find_existing_user(model_user=user):
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
            existing_user = (
                self._db.query(User)
                .filter_by(
                    application_instance=application_instance,
                    user_id=user_id,
                )
                .one()
            )
        except NoResultFound as err:
            raise UserNotFound() from err

        return existing_user

    def _find_existing_user(self, model_user: User) -> Optional[User]:
        return (
            self._db.query(User)
            .filter_by(
                application_instance_id=model_user.application_instance_id,
                user_id=model_user.user_id,
            )
            .one_or_none()
        )


def factory(_context, request):
    """Service factory for the UserService."""

    return UserService(request.db, request.registry.settings["h_authority"])
