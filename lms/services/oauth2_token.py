import datetime
import logging
from functools import lru_cache

from lms.models import ApplicationInstance, OAuth2Token
from lms.services import OAuth2TokenError

LOG = logging.getLogger(__name__)


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
                application_instance=self._application_instance,
                user_id=self._user_id,
            )
            self._db.add(oauth2_token)

        oauth2_token.access_token = access_token
        oauth2_token.refresh_token = refresh_token
        oauth2_token.expires_in = expires_in
        oauth2_token.received_at = datetime.datetime.utcnow()

    @lru_cache(maxsize=1)
    def get(self):
        """
        Return the user's saved OAuth 2 token from the DB.

        :raise OAuth2TokenError: if we don't have an OAuth 2 token for the user
        """
        token = (
            self._db.query(OAuth2Token)
            .join(ApplicationInstance)
            .filter(
                # We don't query by application_instance but any token belonging to an AI with the same GUID
                ApplicationInstance.tool_consumer_instance_guid
                == self._application_instance.tool_consumer_instance_guid,
                OAuth2Token.user_id == self._user_id,
            )
            # We might find more that one token if we created them for multiple installs, prefere the latest.
            .order_by(OAuth2Token.id.desc())
            .first()
        )
        if not token:
            raise OAuth2TokenError("We don't have an OAuth 2 token for this user")

        return token


def oauth2_token_service_factory(_context, request):
    return OAuth2TokenService(
        request.db, request.lti_user.application_instance, request.lti_user.user_id
    )
