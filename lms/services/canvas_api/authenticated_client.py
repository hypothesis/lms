from copy import deepcopy

import marshmallow
from marshmallow import fields
from requests import Request

from lms.services import CanvasAPIAccessTokenError
from lms.validation import RequestsResponseSchema


class CanvasTokenResponseSchema(RequestsResponseSchema):
    """Schema for validating OAuth 2 token responses from Canvas."""

    access_token = fields.Str(required=True)
    refresh_token = fields.Str()
    expires_in = fields.Integer()

    @marshmallow.validates("expires_in")
    def validate_quantity(self, expires_in):  # pylint:disable=no-self-use
        if expires_in <= 0:
            raise marshmallow.ValidationError("expires_in must be greater than 0")


class AuthenticatedClient:
    """
    A client for making authenticated calls to the Canvas API.

    All methods in the authenticated client may raise:

    :raise CanvasAPIAccessTokenError: if the request fails because our
         Canvas API access token for the user is missing, expired, or has
         been deleted
    :raise CanvasAPIServerError: if the request fails for any other reason
    """

    def __init__(
        self, basic_client, token_store, client_id, client_secret, redirect_uri
    ):
        self._api = basic_client
        self._token_store = token_store

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
        :raise CanvasAPIAccessTokenError: if the request fails because our
             Canvas API access token for the user is missing, expired, or has
             been deleted
        :return: JSON deserialised object
        """
        request = self._api.make_request(method, path, schema, params)
        request.headers[
            "Authorization"
        ] = f"Bearer {self._token_store.get().access_token}"

        try:
            return self._api.send_and_validate(request, schema)

        except CanvasAPIAccessTokenError:
            refresh_token = self._token_store.get().refresh_token
            if not refresh_token:
                raise

            new_request = deepcopy(request)
            new_access_token = self.get_refreshed_token(refresh_token)
            new_request.headers["Authorization"] = f"Bearer {new_access_token}"

            return self._api.send_and_validate(new_request, schema)

    def get_token(self, authorization_code):
        """
        Get an access token for the current LTI user.

        :param authorization_code: The Canvas API OAuth 2.0 authorization code to
            exchange for an access token
        """
        # For documentation of this request see:
        # https://canvas.instructure.com/doc/api/file.oauth_endpoints.html#post-login-oauth2-token
        self._send_token_request(
            grant_type="authorization_code",
            code=authorization_code,
            redirect_uri=self._redirect_uri,
            replace_tokens=True,
        )

    def get_refreshed_token(self, refresh_token):
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

        request = Request("POST", self._token_url, params=params).prepare()
        parsed_params = self._api.send_and_validate(request, CanvasTokenResponseSchema)

        self._token_store.save(
            parsed_params["access_token"],
            parsed_params.get("refresh_token", refresh_token),
            parsed_params.get("expires_in"),
        )

        return parsed_params["access_token"]

    @property
    def _token_url(self):
        """Return the URL of the Canvas API's token endpoint."""

        return self._api.get_url("login/oauth2/token", url_stub="")
