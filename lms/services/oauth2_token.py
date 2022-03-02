import datetime
from functools import lru_cache

from sqlalchemy.orm.exc import NoResultFound

from lms.models import OAuth2Token
from lms.services import OAuth2TokenError


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

    def save(self, access_token, refresh_token, expires_in):
        """
        Save an OAuth 2 token to the DB.

        If there's already an OAuth2Token for the user's consumer key and user
        ID then overwrite its values. Otherwise create a new OAuth2Token and
        add it to the DB.
        """
        try:
            oauth2_token = self.get()
        except OAuth2TokenError:
            oauth2_token = OAuth2Token(
                consumer_key=self._application_instance.consumer_key,
                user_id=self._user_id,
            )
            self._db.add(oauth2_token)

        oauth2_token.application_instance_id = self._application_instance.id
        oauth2_token.access_token = access_token
        oauth2_token.refresh_token = refresh_token
        oauth2_token.expires_in = expires_in
        oauth2_token.received_at = datetime.datetime.utcnow()

    @lru_cache
    def get(self):
        """
        Return the user's saved OAuth 2 token from the DB.

        :raise OAuth2TokenError: if we don't have an OAuth 2 token for the user
        """
        try:
            return (
                self._db.query(OAuth2Token)
                .filter_by(
                    consumer_key=self._application_instance.consumer_key,
                    user_id=self._user_id,
                )
                .one()
            )
        except NoResultFound as err:
            raise OAuth2TokenError(
                "We don't have an OAuth 2 token for this user"
            ) from err


def oauth2_token_service_factory(_context, request):
    return OAuth2TokenService(
        request.db,
        request.find_service(name="application_instance").get_current(),
        request.lti_user.user_id,
    )
