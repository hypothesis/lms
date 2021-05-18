import datetime

import requests
from sqlalchemy.orm.exc import NoResultFound

from lms.models import OAuth2Token
from lms.services.exceptions import ProxyAPIAccessTokenError


class BlackboardAPIClient:  # pylint:disable=too-many-instance-attributes
    def __init__(
        self,
        blackboard_host,
        client_id,
        client_secret,
        redirect_uri,
        consumer_key,
        user_id,
        db,
    ):  # pylint:disable=too-many-arguments
        self.blackboard_host = blackboard_host
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.consumer_key = consumer_key
        self.user_id = user_id

        self._db = db
        self._session = requests.Session()

    def get_token(self, authorization_code):
        request = requests.Request(
            "POST",
            f"https://{self.blackboard_host}/learn/api/public/v1/oauth2/token",
            data={
                "grant_type": "authorization_code",
                "redirect_uri": self.redirect_uri,
                "code": authorization_code,
            },
            auth=(self.client_id, self.client_secret),
        ).prepare()

        response = self._session.send(request, timeout=9)
        response.raise_for_status()

        json = response.json()
        access_token = json["access_token"]
        refresh_token = json["refresh_token"]
        expires_in = json["expires_in"]

        self._save(access_token, refresh_token, expires_in)

    def _oauth2_token(self):
        try:
            return (
                self._db.query(OAuth2Token)
                .filter_by(consumer_key=self.consumer_key, user_id=self.user_id)
                .one()
            )
        except NoResultFound as err:
            raise ProxyAPIAccessTokenError(
                explanation="We don't have a Blackboard API access token for this user",
                response=None,
            ) from err

    def _save(self, access_token, refresh_token, expires_in):
        try:
            oauth2_token = self._oauth2_token()
        except ProxyAPIAccessTokenError:
            oauth2_token = OAuth2Token(
                consumer_key=self.consumer_key, user_id=self.user_id
            )
            self._db.add(oauth2_token)

        oauth2_token.access_token = access_token
        oauth2_token.refresh_token = refresh_token
        oauth2_token.expires_in = expires_in
        oauth2_token.received_at = datetime.datetime.utcnow()


def factory(_context, request):
    application_instance = request.find_service(name="application_instance").get()
    settings = request.registry.settings
    lti_user = request.lti_user

    return BlackboardAPIClient(
        blackboard_host=application_instance.lms_host(),
        client_id=settings["blackboard_api_client_id"],
        client_secret=settings["blackboard_api_client_secret"],
        redirect_uri=request.route_url("blackboard_api.oauth.callback"),
        consumer_key=lti_user.oauth_consumer_key,
        user_id=lti_user.user_id,
        db=request.db,
    )
