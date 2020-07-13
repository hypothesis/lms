import datetime
from urllib.parse import urlparse, urlencode

import marshmallow
import requests
from marshmallow import fields
from requests import Session, RequestException
from sqlalchemy.orm.exc import NoResultFound

from lms.models import OAuth2Token
from lms.services import CanvasAPIAccessTokenError, CanvasAPIError
from lms.validation import RequestsResponseSchema, ValidationError


class AuthTokenFactory:
    def __init__(self, client_id, client_secret, redirect_uri):
        self._client_id = client_id
        self._client_secret = client_secret
        self.redirect_uri = redirect_uri

    def authorization_code(self, authorization_code):
        return {
            "grant_type": "authorization_code",
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "redirect_uri": self._redirect_uri,
            "code": authorization_code,
            "replace_tokens": True,
        }

    def refresh_token(self, refresh_token):
        return {
            "grant_type": "refresh_token",
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "refresh_token": refresh_token,
        }


class CanvasAPIBasicClient:
    PAGINATION_PER_PAGE = 1000
    """The number of items to request at one time.

     This only applies for calls which return more than one, and is subject
     to a secret internal limit applied by Canvas (might be 100?)."""

    PAGINATION_MAXIMUM_REQUESTS = 25
    """The maximum number of calls to make before giving up."""

    def __init__(self, canvas_host):
        self._canvas_host = canvas_host

    def send(self, method, path, schema, params):
        # Always request the maximum items per page for requests which return
        # more than one thing
        if schema.many:
            if params is None:
                params = {}

            params["per_page"] = self.PAGINATION_PER_PAGE

        # TODO! - This should use the session!
        return requests.Request(method, self.get_url(path, params)).prepare()

    def get_url(self, path, params=None, url_stub="/api/v1"):
        return f"https://{self._canvas_host}{url_stub}/{path}" + (
            "?" + urlencode(params) if params else ""
        )

    def _validated_response(self, request, schema, request_depth=1):
        """
        Send a Canvas API request and validate and return the response.

        If a validation schema is given then the parsed and validated response
        params will be available on the returned response object as
        `response.parsed_params` (a dict).

        :param request: a prepared request to some Canvas API endpoint
        :param schema: The schema class to validate the contents of the response
            with.
        :param request_depth: The number of requests made so far for pagination
        """

        try:
            response = self._session.send(request, timeout=9)
            response.raise_for_status()
        except RequestException as err:
            CanvasAPIError.raise_from(err)

        result = None
        try:
            result = schema(response).parse()
        except ValidationError as err:
            CanvasAPIError.raise_from(err)

        # Handle pagination links. See:
        # https://canvas.instructure.com/doc/api/file.pagination.html
        next_url = response.links.get("next")
        if next_url:
            # We can only append results if the response is expecting multiple
            # items from the Canvas API
            if not schema.many:
                CanvasAPIError.raise_from(
                    TypeError(
                        "Canvas returned paginated results but we expected a single value"
                    )
                )

            # Don't make requests forever
            if request_depth < self.PAGINATION_MAXIMUM_REQUESTS:
                request.url = next_url["url"]
                result.extend(
                    self._validated_response(
                        request, schema, request_depth=request_depth + 1
                    )
                )

        return result


class CanvasAPIAuthenticatedClient(CanvasAPIBasicClient):
    """
    A client for making authenticated calls to the Canvas API.

    All methods in the authenticated client may raise:

    :raise CanvasAPIAccessTokenError: if the request fails because our
         Canvas API access token for the user is missing, expired, or has
         been deleted
    :raise CanvasAPIServerError: if the request fails for any other reason
    """

    def __init__(self, request):
        ai_getter = request.find_service(name="ai_getter")

        # For all requests
        self._session = Session()
        self._canvas_url = urlparse(ai_getter.lms_url()).netloc

        # For making token requests
        self._client_id = ai_getter.developer_key()
        self._client_secret = ai_getter.developer_secret()
        self._redirect_uri = request.route_url("canvas_oauth_callback")

        # For saving tokens
        self._consumer_key = request.lti_user.oauth_consumer_key
        self._user_id = request.lti_user.user_id
        self._db = request.db

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
        request = self._send_unauthenticated(method, path, schema, params)
        request.headers["Authorization"] = f"Bearer {self._oauth2_token.access_token}"

        try:
            return self._validated_response(request, schema)

        except CanvasAPIAccessTokenError:
            refresh_token = self._oauth2_token.refresh_token
            if not refresh_token:
                raise

            new_access_token = self._get_refreshed_token(refresh_token)
            request.headers["Authorization"] = f"Bearer {new_access_token}"

            return self._validated_response(request, schema)

    def get_token(self, authorization_code):
        """
        Get an access token for the current LTI user.

        :param authorization_code: The Canvas API OAuth 2.0 authorization code to
            exchange for an access token
        """
        # For documentation of this request see:
        # https://canvas.instructure.com/doc/api/file.oauth_endpoints.html#post-login-oauth2-token

        parsed_params = self._validated_response(
            requests.Request(
                "POST",
                self._token_url,
                params={
                    "grant_type": "authorization_code",
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                    "redirect_uri": self._redirect_uri,
                    "code": authorization_code,
                    "replace_tokens": True,
                },
            ).prepare(),
            self._CanvasTokenResponseSchema,
        )

        self._save_auth_tokens(
            parsed_params["access_token"],
            parsed_params.get("refresh_token"),
            parsed_params.get("expires_in"),
        )

    def _get_refreshed_token(self, refresh_token):
        parsed_params = self._validated_response(
            requests.Request(
                "POST",
                self._token_url,
                params={
                    "grant_type": "refresh_token",
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                    "refresh_token": refresh_token,
                },
            ).prepare(),
            self._CanvasTokenResponseSchema,
        )

        new_access_token = parsed_params["access_token"]

        self._save_auth_tokens(
            new_access_token,
            parsed_params.get("refresh_token", refresh_token),
            parsed_params.get("expires_in"),
        )

        return new_access_token

    class _CanvasTokenResponseSchema(RequestsResponseSchema):
        """Schema for validating OAuth 2 token responses from Canvas."""

        access_token = fields.Str(required=True)
        refresh_token = fields.Str()
        expires_in = fields.Integer()

        @marshmallow.validates("expires_in")
        def validate_quantity(self, expires_in):  # pylint:disable=no-self-use
            if expires_in <= 0:
                raise marshmallow.ValidationError("expires_in must be greater than 0")


    def _save_auth_tokens(self, access_token, refresh_token, expires_in):
        """
        Save an access token and refresh token to the DB.

        If there's already an `OAuth2Token` for the consumer key and user id
        then overwrite its values. Otherwise create a new `OAuth2Token` and
        add it to the DB.
        """
        try:
            oauth2_token = self._oauth2_token
        except CanvasAPIAccessTokenError:
            oauth2_token = OAuth2Token(
                consumer_key=self._consumer_key, user_id=self._user_id
            )
            self._db.add(oauth2_token)

        oauth2_token.access_token = access_token
        oauth2_token.refresh_token = refresh_token
        oauth2_token.expires_in = expires_in
        oauth2_token.received_at = datetime.datetime.utcnow()

    @property
    def _oauth2_token(self):
        """
        Return the user's saved access and refresh tokens from the DB.

        :raise CanvasAPIAccessTokenError: if we don't have an access token for the user
        """
        try:
            return (
                self._db.query(OAuth2Token)
                .filter_by(consumer_key=self._consumer_key, user_id=self._user_id)
                .one()
            )
        except NoResultFound as err:
            raise CanvasAPIAccessTokenError(
                explanation="We don't have a Canvas API access token for this user",
                response=None,
            ) from err


    @property
    def _token_url(self):
        """Return the URL of the Canvas API's token endpoint."""

        return self._get_url("login/oauth2/token", url_stub="")