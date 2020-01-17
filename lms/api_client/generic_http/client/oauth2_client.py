from contextlib import contextmanager
from typing import NamedTuple

from requests import HTTPError

from lms.api_client.generic_http.client.json_client import JSONHTTPClient
from lms.api_client.generic_http.exceptions import AuthenticationFailure
from lms.api_client.generic_http.retriable import retriable


class OAuth2Settings(NamedTuple):
    client_id: str
    client_secret: str
    redirect_uri: str


class OAuth2Tokens:
    def __init__(self, access_token=None, refresh_token=None, update_callback=None):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.update_callback = update_callback

    def update(self, tokens):
        self.access_token = tokens["access_token"]
        self.refresh_token = tokens["refresh_token"]

        if self.update_callback:
            self.update_callback(tokens)


class OAuth2Client(JSONHTTPClient):
    authorization_code_endpoint = None
    access_token_endpoint = None

    def __init__(self, settings, tokens, host, scheme="https", url_stub=None):
        super().__init__(host, scheme, url_stub)
        self.settings = settings
        self.tokens = tokens
        self.in_session = False

    @contextmanager
    def session(self):
        with super().session() as session:
            # Add the Authorization header
            self._set_session_token()

            # Return a context manager enabling retries when we encounter
            # retriable errors such as AuthenticationFailure
            with retriable.retry_handler(self._retry_handler):
                yield session

    def call(self, method, path, query=None, headers=None, **options):
        options.update(
            {"method": method, "path": path, "query": query, "headers": headers,}
        )

        try:
            return super().call(**options)

        except HTTPError as e:
            if e.response.status_code != 401:
                raise

            # This exception is 'retriable' which means it can be caught by
            # the 'retriable' decorator
            raise AuthenticationFailure(e.args[0], kwargs=options) from e

    def get_authorize_code_url(self):
        if self.authorization_code_endpoint is None:
            raise NotImplementedError()

        return self.get_url(
            self.authorization_code_endpoint,
            query={
                "response_type": "code",
                "client_id": self.settings.client_id,
                "redirect_uri": self.settings.redirect_uri,
            },
        )

    def get_tokens(self, code):
        return self._get_tokens({"code": code, "grant_type": "authorization_code",})

    def refresh_tokens(self):
        if self.tokens.refresh_token is None:
            raise TypeError("Cannot refresh without refresh_token")

        return self._get_tokens(
            {"refresh_token": self.tokens.refresh_token, "grant_type": "refresh_token",}
        )

    def _get_tokens(self, query):
        if self.access_token_endpoint is None:
            raise NotImplementedError()

        query["redirect_uri"] = self.settings.redirect_uri

        tokens = self.call(
            "POST",
            self.access_token_endpoint,
            query=query,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            auth=(self.settings.client_id, self.settings.client_secret),
        )

        self.tokens.update(tokens)
        self._set_session_token()

        return tokens

    def _retry_handler(self, retriable_exception):
        self.refresh_tokens()

        # Attempt the call again
        return self.call(**retriable_exception.kwargs)

    def _set_session_token(self):
        if not self.tokens.access_token or self._session is None:
            return

        self._session.headers["Authorization"] = f"Bearer {self.tokens.access_token}"
