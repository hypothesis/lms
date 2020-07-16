import datetime

from sqlalchemy.orm.exc import NoResultFound

from lms.models import OAuth2Token
from lms.services import CanvasAPIAccessTokenError


class TokenStore:
    def __init__(self, db, consumer_key, user_id):
        self._db = db
        self._consumer_key = consumer_key
        self._user_id = user_id

    def save(self, access_token, refresh_token, expires_in):
        """
        Save an access token and refresh token to the DB.

        If there's already an `OAuth2Token` for the consumer key and user id
        then overwrite its values. Otherwise create a new `OAuth2Token` and
        add it to the DB.
        """
        try:
            oauth2_token = self.get()
        except CanvasAPIAccessTokenError:
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
        Return the user's saved access and refresh tokens from the DB.

        :raise CanvasAPIAccessTokenError: if we don't have an access token for the user
        """
        try:
            return (
                self._db.query(OAuth2Token)
                .filter_by(consumer_key=self._consumer_key, user_id=self._user_id)
                .one()
            )
        except NoResultFound as err:
            raise CanvasAPIAccessTokenError(
                explanation="We don't have a Canvas API access token for this user",
                response=None,
            ) from err
