from contextlib import contextmanager

from lms.api_client.generic_http.retriable import retriable


class OAuth2Manager:
    access_token = None
    refresh_token = None
    in_session = False

    def __init__(self, ws, client_id, client_secret, redirect_uri, token_callback=None):
        self.ws = ws

        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.token_callback = token_callback

    def get_authorize_code_url(self):
        return self.ws.get_authorize_code_url(
            client_id=self.client_id, redirect_uri=self.redirect_uri
        )

    def refresh_tokens(self):
        if self.refresh_token is None:
            raise TypeError("Cannot refresh without refresh_token")

        return self._update_tokens(
            self.ws.refresh_tokens(
                self.refresh_token,
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri,
            )
        )

    def get_tokens(self, code):
        return self._update_tokens(
            self.ws.get_tokens(
                code,
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri,
            )
        )

    def set_tokens(self, access_token, refresh_token):
        self.access_token = access_token
        self.refresh_token = refresh_token

        # TODO! - This seems grotty
        if self.in_session:
            self.ws.set_access_token(self.access_token)

        return self

    @contextmanager
    def session(self):
        self.in_session = True

        # Add an HTTP session so we are nice and fast for multiple calls
        with self.ws.session():
            self.ws.set_access_token(self.access_token)

            # Return a context manager enabling retries
            with retriable.retry_handler(self._retry_handler):
                yield

        self.in_session = False

    def _retry_handler(self, retriable_exception):
        """Context manager."""

        self.refresh_tokens()

        # Attempt the call again
        return self.ws.call(**retriable_exception.kwargs)

    def _update_tokens(self, token_response):
        self.set_tokens(token_response["access_token"], token_response["refresh_token"])

        if self.token_callback:
            self.token_callback(token_response)

        return token_response
