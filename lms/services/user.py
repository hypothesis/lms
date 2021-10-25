from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Session

from lms.models import LTIUser
from lms.models.user import User
from lms.services.application_instance import ApplicationInstanceService


@dataclass
class UserService:
    """
    A service for working with users.

    At the moment this is purely used for recording/reporting purposes.
    """

    application_instance_service: ApplicationInstanceService
    db_session: Session
    h_authority: str

    def store_lti_user(self, lti_user: LTIUser):
        """
        Store a record of having seen a particular user.

        :param lti_user: LTIUser to store
        """
        new_user = self._from_lti_user(lti_user)

        if existing_user := self._find_existing_user(model_user=new_user):
            # Update the existing user from the fields which can change on a
            # new one
            existing_user.roles = new_user.roles

        else:
            self.db_session.add(new_user)

    def _find_existing_user(self, model_user: User) -> Optional[User]:
        return (
            self.db_session.query(User)
            .filter_by(
                application_instance=model_user.application_instance,
                user_id=model_user.user_id,
                h_userid=model_user.h_userid,
            )
            .one_or_none()
        )

    def _from_lti_user(self, lti_user: LTIUser) -> User:
        return User(
            application_instance=self.application_instance_service.get_by_consumer_key(
                lti_user.oauth_consumer_key
            ),
            user_id=lti_user.user_id,
            roles=lti_user.roles,
            h_userid=lti_user.h_user.userid(self.h_authority),
        )


def factory(_context, request):
    """Service factory for the UserService."""

    return UserService(
        application_instance_service=request.find_service(name="application_instance"),
        db_session=request.db,
        h_authority=request.registry.settings["h_authority"],
    )
