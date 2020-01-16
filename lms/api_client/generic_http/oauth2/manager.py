from lms.api_client.generic_http.retriable import retriable


class OAuth2Manager:
    def __init__(self, ws, client_id, client_secret, redirect_uri, refresh_token=None):
        self.ws = ws

        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.refresh_token = refresh_token

    def get_authorize_code_url(self):
        return self.ws.get_authorize_code_url(
            client_id=self.client_id, redirect_uri=self.redirect_uri
        )

    def refresh_tokens(self):
        if self.refresh_token is None:
            raise TypeError("Cannot refresh without refresh_token")

        return self._store_tokens(
            self.ws.refresh_tokens(
                self.refresh_token,
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri,
            )
        )

    def get_tokens(self, code):
        return self._store_tokens(
            self.ws.get_tokens(
                code,
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri,
            )
        )

    def retry(self, retriable_exception):
        """Context manager."""

        self.refresh_tokens()

        # Attempt the call again
        return self.ws.oauth2_call(**retriable_exception.kwargs)

    def _store_tokens(self, tokens):
        print("NEW TOKENS", tokens)

        # Update the web service access token
        self.ws.access_token = tokens["access_token"]

        # Update our refresh token
        self.refresh_token = tokens["refresh_token"]

        return tokens

    def retry_session(self):
        return retriable.retry_handler(self.retry)
