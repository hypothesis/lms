from base64 import b64encode

from requests import HTTPError

from lms.api_client.generic_http.exceptions import BadBearerToken
from lms.api_client.generic_http.json_client import JSONHTTPClient


class OAuth2Client(JSONHTTPClient):
    authorization_code_endpoint = None
    access_token_endpoint = None

    def __init__(self, host, scheme="https", url_stub=None, access_token=None):
        self.access_token = access_token

        super().__init__(host, scheme, url_stub)

    def oauth2_call(self, method, path, query=None, headers=None):
        if not self.access_token:
            raise TypeError("Access token required")

        if headers is None:
            headers = {}

        headers["Authorization"] = f"Bearer {self.access_token}"

        try:
            return self.call(method, path, query, headers)
        except HTTPError as e:
            if e.response.status_code != 401:
                raise

            raise BadBearerToken(
                e.args[0],
                kwargs={
                    "method": method,
                    "path": path,
                    "query": query,
                    "headers": headers,
                },
            ) from e

    def get_tokens(self, code, client_id, client_secret, redirect_uri):
        return self._get_tokens(
            {
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
            },
            client_id,
            client_secret,
        )

    def refresh_tokens(self, refresh_token, client_id, client_secret, redirect_uri):
        return self._get_tokens(
            {
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
                "redirect_uri": redirect_uri,
            },
            client_id,
            client_secret,
        )

    def _get_tokens(self, query, client_id, client_secret):
        if self.access_token_endpoint is None:
            raise NotImplementedError()

        return self.call(
            "POST",
            self.access_token_endpoint,
            query=query,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": self.basic_auth_header(client_id, client_secret),
            },
        )

    def get_authorize_code_url(self, client_id, redirect_uri):
        if self.authorization_code_endpoint is None:
            raise NotImplementedError()

        return self.get_url(
            self.authorization_code_endpoint,
            query={
                "response_type": "code",
                "client_id": client_id,
                "redirect_uri": redirect_uri,
            },
        )

    @classmethod
    def basic_auth_header(self, client_id, client_secret):
        # TODO! Will requests do this for us?
        return "Basic ".encode("ascii") + b64encode(
            f"{client_id}:{client_secret}".encode("ascii")
        )
