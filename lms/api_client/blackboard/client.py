from lms.api_client.blackboard.api import APIRoot
from lms.api_client.generic_http.oauth2.client import OAuth2Client


class BlackboardClient(OAuth2Client):
    authorization_code_endpoint = "oauth2/authorizationcode"
    access_token_endpoint = "oauth2/token"

    def __init__(self, host, access_token=None):
        super().__init__(
            host,
            scheme="https",
            url_stub="learn/api/public/v1",
            access_token=access_token,
        )

    def api(self):
        return APIRoot(self)
