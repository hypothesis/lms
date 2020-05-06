import datetime
from urllib.parse import urlencode, urlparse

import marshmallow
import requests
from marshmallow import EXCLUDE, Schema, fields, post_load, validate, validates_schema
from requests import RequestException, Session
from sqlalchemy.orm.exc import NoResultFound

from lms.models import OAuth2Token
from lms.services import CanvasAPIAccessTokenError
from lms.services.exceptions import CanvasAPIError
from lms.validation import RequestsResponseSchema, ValidationError

__all__ = ["CanvasAPIClient"]


class _SectionSchema(Schema):
    """
    Schema for an individual course section dict.

    These course section dicts appear in various different Canvas API responses.
    This _SectionSchema class is used as a base class or nested schema by
    various schemas below for Canvas API responses that contain section dicts.
    """

    class Meta:  # pylint:disable=too-few-public-methods
        unknown = EXCLUDE

    id = fields.Int(required=True)
    name = fields.String(required=True)


# pylint: disable=too-many-instance-attributes
class _CanvasAPIAuthenticatedClient:
    """
    A client for making authenticated calls to the Canvas API.

    All methods in the authenticated client may raise:

    :raise CanvasAPIAccessTokenError: if the request fails because our
         Canvas API access token for the user is missing, expired, or has
         been deleted
    :raise CanvasAPIServerError: if the request fails for any other reason
    """

    PAGINATION_PER_PAGE = 1000
    """The number of items to request at one time.

     This only applies for calls which return more than one, and is subject
     to a secret internal limit applied by Canvas (might be 100?)."""

    PAGINATION_MAXIMUM_REQUESTS = 25
    """The maximum number of calls to make before giving up."""

    def __init__(self, _context, request):
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

        self._save(
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

        self._save(
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

    def make_authenticated_request(self, method, path, schema, params=None):
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
        request = self._make_request(method, path, schema, params)
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

    def _make_request(self, method, path, schema, params):
        # Always request the maximum items per page for requests which return
        # more than one thing
        if schema.many:
            if params is None:
                params = {}

            params["per_page"] = self.PAGINATION_PER_PAGE

        return requests.Request(method, self._get_url(path, params)).prepare()

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

    def _save(self, access_token, refresh_token, expires_in):
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

    def _get_url(self, path, params=None, url_stub="/api/v1"):
        return f"https://{self._canvas_url}{url_stub}/{path}" + (
            "?" + urlencode(params) if params else ""
        )

    @property
    def _token_url(self):
        """Return the URL of the Canvas API's token endpoint."""

        return self._get_url("login/oauth2/token", url_stub="")


class CanvasAPIClient(_CanvasAPIAuthenticatedClient):
    """
    A client for making calls to the CanvasAPI.

    All methods may raise:

    :raise CanvasAPIAccessTokenError: if we can't get the list of sections
            because we don't have a working Canvas API access token for the user
    :raise CanvasAPIServerError: if we do have an access token but the
            Canvas API request fails for any other reason
    """

    def authenticated_users_sections(self, course_id):
        """
        Return the authenticated user's sections for the given course_id.

        :param course_id: the Canvas course_id of the course to look in
        :return: a list of raw section dicts as received from the Canvas API
        :rtype: list(dict)
        """

        # Canvas's sections API
        # (https://canvas.instructure.com/doc/api/sections.html) only allows
        # you to get _all_ of a course's sections, it doesn't provide a way to
        # get only the sections that the authenticated user belongs to. So we
        # have to get the authenticated user's sections from part of the
        # response from a courses API endpoint instead.
        #
        # Canvas's "Get a single course" API is capable of doing this if the
        # ?include[]=sections query param is given:
        #
        #    https://canvas.instructure.com/doc/api/courses.html#method.courses.show
        #
        # The ?include[]=sections query param is documented elsewhere (in the
        # "List your courses" API:
        # https://canvas.instructure.com/doc/api/courses.html#method.courses.index)
        # as:
        #
        #    "Section enrollment information to include with each Course.
        #    Returns an array of hashes containing the section ID (id), section
        #    name (name), start and end dates (start_at, end_at), as well as the
        #    enrollment type (enrollment_role, e.g. 'StudentEnrollment')."
        #
        # In practice ?include[]=sections seems to add a "sections" key to the
        # API response that is a list of section dicts, one for each section
        # the authenticated user is currently enrolled in, each with the
        # section's "id" and "name" among other fields.
        #
        # **We don't know what happens if the user belongs to a really large
        # number of sections**. Does the list of sections embedded within the
        # get course API response just get really long? Does it get truncated?
        # Can you paginate through it somehow? This seems edge-casey enough
        # that we're ignoring it for now.

        return self.make_authenticated_request(
            "GET",
            f"courses/{course_id}",
            params={"include[]": "sections"},
            schema=self._AuthenticatedUsersSectionsSchema,
        )

    class _AuthenticatedUsersSectionsSchema(RequestsResponseSchema):
        """Schema for the "authenticated user's sections" responses."""

        sections = fields.List(
            fields.Nested(_SectionSchema),
            validate=validate.Length(min=1),
            required=True,
        )

        @post_load
        def post_load(self, data, **_kwargs):  # pylint:disable=no-self-use
            # Return the contents of sections without the key

            return data["sections"]

    def course_sections(self, course_id):
        """
        Return all the sections for the given course_id.

        :param course_id: the Canvas course_id of the course to look in
        :return: a list of raw section dicts as received from the Canvas API
        :rtype: list(dict)
        """
        # For documentation of this request see:
        # https://canvas.instructure.com/doc/api/sections.html#method.sections.index

        return self.make_authenticated_request(
            "GET", f"courses/{course_id}/sections", schema=self._CourseSectionsSchema,
        )

    class _CourseSectionsSchema(RequestsResponseSchema, _SectionSchema):
        """Schema for the "list course sections" responses."""

        many = True

        @validates_schema(pass_many=True)
        def _validate_length(self, data, **kwargs):  # pylint:disable=no-self-use
            # If we get as far as this method then data is guaranteed to be a list
            # so the only way it can be falsey is if it's an empty list.
            if not data:
                raise marshmallow.ValidationError("Shorter than minimum length 1.")

    def users_sections(self, user_id, course_id):
        """
        Return all the given user's sections for the given course_id.

        :param user_id: the Canvas user_id of the user whose sections you want
        :param course_id: the Canvas course_id of the course to look in
        :return: a list of raw section dicts as received from the Canvas API
        :rtype: list(dict)
        """
        # For documentation of this request see:
        # https://canvas.instructure.com/doc/api/courses.html#method.courses.user

        return self.make_authenticated_request(
            "GET",
            f"courses/{course_id}/users/{user_id}",
            params={"include[]": "enrollments"},
            schema=self._UsersSectionsSchema,
        )

    class _UsersSectionsSchema(RequestsResponseSchema):
        """Schema for the "user's course sections" responses."""

        class _EnrollmentSchema(Schema):
            """Schema for extracting a section ID from an enrollment dict."""

            class Meta:  # pylint:disable=too-few-public-methods
                unknown = EXCLUDE

            course_section_id = fields.Int(required=True)

        enrollments = fields.List(
            fields.Nested(_EnrollmentSchema),
            validate=validate.Length(min=1),
            required=True,
        )

        @post_load
        def post_load(self, data, **_kwargs):  # pylint:disable=no-self-use
            # Return a list of section ids in the same style as the course
            # sections (but without names).

            return [
                {"id": enrollment["course_section_id"]}
                for enrollment in data["enrollments"]
            ]

    def list_files(self, course_id):
        """
        Return the list of files for the given `course_id`.

        :param course_id: the Canvas course_id of the course to look in
        :rtype: list(dict)
        """
        # For documentation of this request see:
        # https://canvas.instructure.com/doc/api/files.html#method.files.api_index

        return self.make_authenticated_request(
            "GET",
            f"courses/{course_id}/files",
            params={"content_types[]": "application/pdf"},
            schema=self._ListFilesSchema,
        )

    class _ListFilesSchema(RequestsResponseSchema):
        """Schema for the list_files response."""

        many = True

        display_name = fields.Str(required=True)
        id = fields.Integer(required=True)
        updated_at = fields.String(required=True)

    def public_url(self, file_id):
        """
        Get a new temporary public download URL for the file with the given ID.

        :param file_id: the ID of the Canvas file
        :rtype: str
        """
        # For documentation of this request see:
        # https://canvas.instructure.com/doc/api/files.html#method.files.public_url

        return self.make_authenticated_request(
            "GET", f"files/{file_id}/public_url", schema=self._PublicURLSchema
        )["public_url"]

    class _PublicURLSchema(RequestsResponseSchema):
        """Schema for the public_url response."""

        public_url = fields.Str(required=True)
