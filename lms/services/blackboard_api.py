import datetime

import requests
from sqlalchemy.orm.exc import NoResultFound

from lms.models import OAuth2Token
from lms.services.exceptions import BlackboardAPIAccessTokenError



class BlackboardAPIClient:
    def __init__(self, client_id, client_secret, redirect_uri, consumer_key, user_id, db):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.consumer_key = consumer_key
        self.user_id = user_id
        self.db = db

        self._session = requests.Session()

    def get_token(self, authorization_code):
        request = requests.Request(
            "POST",
            "https://blackboard.hypothes.is/learn/api/public/v1/oauth2/token",
            data={
                "grant_type": "authorization_code",
                "redirect_uri": self.redirect_uri,
                "code": authorization_code,
            },
            auth=(self.client_id, self.client_secret),
        ).prepare()

        try:
            response = self._session.send(request, timeout=9)
            response.raise_for_status()
        except requests.RequestException as err:
            raise

        json = response.json()
        access_token = json["access_token"]
        refresh_token = json["refresh_token"]
        expires_in = json["expires_in"]

        self._save(access_token, refresh_token, expires_in)

    def list_files(self, course_id):
        response = requests.get(
            "https://blackboard.hypothes.is/learn/api/public/v1/courses/_5_1/resources",
            headers={"Authorization": f"Bearer {self._oauth2_token.access_token}"}
        )
        results = response.json()["results"]


        response = requests.get(
            "https://blackboard.hypothes.is/learn/api/public/v1/courses/_5_1/contents?recursive=true",
            headers={"Authorization": f"Bearer {self._oauth2_token.access_token}"}
        )
        import pdb; pdb.set_trace()

        return [
            {
                "display_name": file_dict["name"],
                "id": file_dict["id"],
                "updated_at": file_dict["modified"],
            } for file_dict in results
        ]

    def public_url(self, file_id):
        response = requests.get(
                "https://blackboard.hypothes.is/learn/api/public/v1/courses/_5_1/resources",
                headers={"Authorization": f"Bearer {self._oauth2_token.access_token}"}
        )
        results = response.json()["results"]
        for file_ in results:
            if file_["id"] == file_id:
                return file_["downloadUrl"]

        assert False

    @property
    def _oauth2_token(self):
        try:
            return (
                self.db.query(OAuth2Token)
                .filter_by(consumer_key=self.consumer_key, user_id=self.user_id)
                .one()
            )
        except NoResultFound as err:
            raise BlackboardAPIAccessTokenError(
                explanation="We don't have a Blackboard API access token for this user",
                response=None,
            ) from err

    def _save(self, access_token, refresh_token, expires_in):
        try:
            oauth2_token = self._oauth2_token
        except BlackboardAPIAccessTokenError:
            oauth2_token = OAuth2Token(
                consumer_key=self.consumer_key, user_id=self.user_id
            )
            self.db.add(oauth2_token)

        oauth2_token.access_token = access_token
        oauth2_token.refresh_token = refresh_token
        oauth2_token.expires_in = expires_in
        oauth2_token.received_at = datetime.datetime.utcnow()


def blackboard_api_client_service_factory(context, request):
    client_secret = request.registry.settings.get("blackboard_client_secret")
    return BlackboardAPIClient(
        client_id="8baa49c0-fb04-4404-acca-7b9bb51405e0",
        client_secret=client_secret,
        redirect_uri=request.route_url("blackboard_oauth_callback"),
        consumer_key=request.lti_user.oauth_consumer_key,
        user_id=request.lti_user.user_id,
        db=request.db,
    )
