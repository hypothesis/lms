import datetime

from sqlalchemy.orm.exc import NoResultFound

from lms.models import OAuth2Token
from lms.services import OAuth2TokenError


class OAuth2TokenService:
    """Save and retrieve OAuth2Tokens from the DB."""

    def __init__(self, db, consumer_key, user_id):
        """
        Return a new TokenStore.

        :param db: the SQLAlchemy session
        :param consumer_key: the LTI consumer key to use for tokens
        :param user_id: the LTI user ID to user for tokens
        """
        self._db = db
        self._consumer_key = consumer_key
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
                consumer_key=self._consumer_key, user_id=self._user_id
            )
            self._db.add(oauth2_token)

        oauth2_token.access_token = access_token
        oauth2_token.refresh_token = refresh_token
        oauth2_token.expires_in = expires_in
        oauth2_token.received_at = datetime.datetime.utcnow()

    def get(self):
        """
        Return the user's saved OAuth 2 token from the DB.

        :raise OAuth2TokenError: if we don't have an OAuth 2 token for the user
        """
        try:
            return (
                self._db.query(OAuth2Token)
                .filter_by(consumer_key=self._consumer_key, user_id=self._user_id)
                .one()
            )
        except NoResultFound as err:
            raise OAuth2TokenError(
                "We don't have an OAuth 2 token for this user"
            ) from err


def oauth2_token_service_factory(_context, request):
    return OAuth2TokenService(
        request.db, request.lti_user.oauth_consumer_key, request.lti_user.user_id
    )
