from lms.api_client.blackboard_classic.api import APIRoot
from lms.api_client.generic_http.client.oauth2_client import OAuth2Client


class BlackboardClassicClient(OAuth2Client):
    authorization_code_endpoint = "oauth2/authorizationcode"
    access_token_endpoint = "oauth2/token"

    def __init__(self, host, settings, tokens):
        super().__init__(
            settings=settings,
            tokens=tokens,
            host=host,
            scheme="https",
            url_stub="learn/api/public/v1",
        )

    def api(self):
        return APIRoot(self)
