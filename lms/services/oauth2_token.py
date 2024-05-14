import datetime
from functools import lru_cache

from sqlalchemy.orm.exc import NoResultFound

from lms.db import LockType, try_advisory_transaction_lock
from lms.models import ApplicationInstance, OAuth2Token
from lms.models.oauth2_token import Service
from lms.services.exceptions import OAuth2TokenError


class OAuth2TokenService:
    """Save and retrieve OAuth2Tokens from the DB."""

    def __init__(self, db, application_instance, user_id):
        """
        Return a new TokenStore.

        :param db: the SQLAlchemy session
        :param application_instance: the ApplicationInstance to use for tokens
        :param user_id: the LTI user ID to user for tokens
        """
        self._db = db
        self._application_instance = application_instance
        self._user_id = user_id

    def save(self, access_token, refresh_token, expires_in, service=Service.LMS):
        """
        Save an OAuth 2 token to the DB.

        If there's already an OAuth2Token for the user's consumer key and user
        ID then overwrite its values. Otherwise create a new OAuth2Token and
        add it to the DB.
        """
        try:
            oauth2_token = self.get(service)
        except OAuth2TokenError:
            oauth2_token = OAuth2Token(
                application_instance=self._application_instance,
                user_id=self._user_id,
                service=service,
            )
            self._db.add(oauth2_token)

        oauth2_token.access_token = access_token
        oauth2_token.refresh_token = refresh_token
        oauth2_token.expires_in = expires_in
        oauth2_token.received_at = datetime.datetime.utcnow()

    @lru_cache(maxsize=1)
    def get(self, service=Service.LMS) -> OAuth2Token:
        """
        Return the user's saved OAuth 2 token from the DB.

        :raise OAuth2TokenError: if we don't have an OAuth 2 token for the user
        """
        try:
            return (
                self._db.query(OAuth2Token)
                .filter_by(
                    application_instance=self._application_instance,
                    user_id=self._user_id,
                    service=service,
                )
                .one()
            )
        except NoResultFound as err:
            raise OAuth2TokenError(
                "We don't have an OAuth 2 token for this user"
            ) from err

    def try_lock_for_refresh(self, service=Service.LMS):
        """
        Attempt to acquire an advisory lock before a token refresh.

        This does not block if the lock is already held. Instead it raises an
        error.

        The lock is released at the end of the current transaction.

        :raise CouldNotAcquireLock: if the lock cannot be immediately acquired
        """
        token = self.get(service)
        try_advisory_transaction_lock(self._db, LockType.OAUTH2_TOKEN_REFRESH, token.id)


def oauth2_token_service_factory(
    _context,
    request,
    application_instance: ApplicationInstance | None = None,
    user_id: str | None = None,
):
    return OAuth2TokenService(
        request.db,
        application_instance or request.lti_user.application_instance,
        user_id or request.lti_user.user_id,
    )
