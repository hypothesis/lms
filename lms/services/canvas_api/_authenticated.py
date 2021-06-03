"""Access to the authenticated parts of the Canvas API."""

from lms.services.exceptions import NoOAuth2Token, ProxyAPIAccessTokenError
from lms.validation.authentication import OAuthTokenResponseSchema


class AuthenticatedClient:
    """
    A client for making authenticated calls to the Canvas API.

    All methods in the authenticated client may raise:

    :raise ProxyAPIAccessTokenError: if the request fails because our
         Canvas API access token for the user is missing, expired, or has
         been deleted
    :raise CanvasAPIServerError: if the request fails for any other reason
    """

    def __init__(  # pylint: disable=too-many-arguments
        self, basic_client, oauth2_token_service, client_id, client_secret, redirect_uri
    ):
        """
        Create an AuthenticatedClient object for making authenticated calls.

        :param basic_client: An instance of BasicClient
        :param oauth2_token_service: The "oauth2_token" service
        :param client_id: The OAuth2 client id
        :param client_secret: The OAuth2 client secret
        :param redirect_uri: The OAuth 2 redirect URI
        """
        self._client = basic_client
        self._oauth2_token_service = oauth2_token_service

        # For making token requests
        self._client_id = client_id
        self._client_secret = client_secret
        self._redirect_uri = redirect_uri

    def send(self, method, path, schema, params=None):
        """
        Send a Canvas API request, and retry it if there are OAuth problems.

        :param method: HTTP method to use (e.g. "POST")
        :param path: The path in the API to make a request to
        :param schema: Schema to apply to the return values
        :param params: Any query parameters to add to the request
        :raise ProxyAPIAccessTokenError: if the request fails because our
            Canvas API access token for the user is missing, expired, or has
            been deleted
        :return: JSON deserialised object
        :raise ProxyAPIAccessTokenError: If a token is required and cannot be
            found / refreshed
        """
        call_args = (method, path, schema, params)

        try:
            oauth2_token = self._oauth2_token_service.get()
        except NoOAuth2Token as err:
            raise ProxyAPIAccessTokenError(
                explanation="We don't have a Canvas API access token for this user",
                response=None,
            ) from err

        access_token = oauth2_token.access_token
        refresh_token = oauth2_token.refresh_token

        try:
            return self._client.send(
                *call_args,
                headers={"Authorization": f"Bearer {access_token}"},
            )
        except ProxyAPIAccessTokenError:
            if not refresh_token:
                raise

        new_access_token = self.get_refreshed_token(refresh_token)

        return self._client.send(
            *call_args,
            headers={"Authorization": f"Bearer {new_access_token}"},
        )

    def get_token(self, authorization_code):
        """
        Get an access token for the current LTI user.

        :param authorization_code: The Canvas API OAuth 2.0 authorization code
            to exchange for an access token
        :return: An access token string
        """
        # For documentation of this request see:
        # https://canvas.instructure.com/doc/api/file.oauth_endpoints.html#post-login-oauth2-token
        return self._send_token_request(
            grant_type="authorization_code",
            code=authorization_code,
            redirect_uri=self._redirect_uri,
            replace_tokens=True,
        )

    def get_refreshed_token(self, refresh_token):
        """
        Get a refreshed access token for the current LTI user.

        :param refresh_token: The Canvas API OAuth 2.0 refresh token from a
            previous token call
        :return: A new access token string
        """
        return self._send_token_request(
            grant_type="refresh_token", refresh_token=refresh_token
        )

    def _send_token_request(self, grant_type, refresh_token=None, **kwargs):
        params = {
            "grant_type": grant_type,
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            **kwargs,
        }

        if refresh_token:
            params["refresh_token"] = refresh_token

        parsed_params = self._client.send(
            "POST",
            "login/oauth2/token",
            url_stub="",
            params=params,
            schema=OAuthTokenResponseSchema,
        )

        self._oauth2_token_service.save(
            parsed_params["access_token"],
            parsed_params.get("refresh_token", refresh_token),
            parsed_params.get("expires_in"),
        )

        return parsed_params["access_token"]
