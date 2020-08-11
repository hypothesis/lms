"""High level access to Canvas API methods."""

import marshmallow
from marshmallow import EXCLUDE, Schema, fields, post_load, validate, validates_schema

from lms.services import CanvasAPIError
from lms.validation import RequestsResponseSchema


class _SectionSchema(Schema):
    """
    Schema for an individual course section dict.

    These course section dicts appear in various different Canvas API responses.
    This _SectionSchema class is used as a base class or nested schema by
    various schemas below for Canvas API responses that contain section dicts.
    """

    class Meta:
        unknown = EXCLUDE

    id = fields.Int(required=True)
    name = fields.String(required=True)


class CanvasAPIClient:
    """
    A client for making calls to the CanvasAPI.

    All methods may raise:

    :raise CanvasAPIAccessTokenError: if we can't get the list of sections
        because we don't have a working Canvas API access token for the user
    :raise CanvasAPIServerError: if we do have an access token but the
        Canvas API request fails for any other reason
    """

    def __init__(self, authenticated_client):
        """
        Create a new CanvasAPIClient.

        :param authenticated_client: An instance of AuthenticatedClient.
        """
        self._client = authenticated_client

    def get_token(self, authorization_code):
        """
        Get an access token for the current LTI user.

        :param authorization_code: The Canvas API OAuth 2.0 authorization code
            to exchange for an access token
        :return: An access token string
        """
        return self._client.get_token(authorization_code)

    # Getting authenticated users sections
    # ------------------------------------
    #
    # [Canvas's sections API](https://canvas.instructure.com/doc/api/sections.html)
    # only allows you to get _all_ of a course's sections, it doesn't provide a
    # way to get only the sections that the authenticated user belongs to. So
    # we have to get the authenticated user's sections from part of the
    # response from a courses API endpoint instead.
    #
    # Canvas's "Get a single course" API is capable of doing this if the
    # `?include[]=sections` query param is given:
    #
    # https://canvas.instructure.com/doc/api/courses.html#method.courses.show
    #
    # The `?include[]=sections` query param is documented elsewhere in the
    # "List your courses" API:
    #
    #  https://canvas.instructure.com/doc/api/courses.html#method.courses.index)
    #
    # >  Section enrollment information to include with each Course.
    #    Returns an array of hashes containing the section ID (id), section
    #    name (name), start and end dates (start_at, end_at), as well as the
    #    enrollment type (enrollment_role, e.g. 'StudentEnrollment').
    #
    # In practice `?include[]=sections` seems to add a "sections" key to the
    # API response that is a list of section dicts, one for each section the
    # authenticated user is currently enrolled in, each with the section's "id"
    # and "name" among other fields.
    #
    # **We don't know what happens if the user belongs to a really large number
    # of sections**. Does the list of sections embedded within the get course
    # API response just get really long? Does it get truncated? Can you
    # paginate through it somehow? This seems edge-casey enough that we're
    # ignoring it for now.

    def authenticated_users_sections(self, course_id):
        """
        Return the authenticated user's sections for the given course_id.

        :param course_id: the Canvas course_id of the course to look in
        :return: a list of raw section dicts as received from the Canvas API
        :rtype: list(dict)
        """

        return self._ensure_sections_unique(
            self._client.send(
                "GET",
                f"courses/{course_id}",
                params={"include[]": "sections"},
                schema=self._AuthenticatedUsersSectionsSchema,
            )
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

        return self._ensure_sections_unique(
            self._client.send(
                "GET",
                f"courses/{course_id}/sections",
                schema=self._CourseSectionsSchema,
            )
        )

    class _CourseSectionsSchema(RequestsResponseSchema, _SectionSchema):
        """Schema for the "list course sections" responses."""

        many = True

        @validates_schema(pass_many=True)
        def _validate_length(self, data, **_kwargs):  # pylint:disable=no-self-use
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

        return self._ensure_sections_unique(
            self._client.send(
                "GET",
                f"courses/{course_id}/users/{user_id}",
                params={"include[]": "enrollments"},
                schema=self._UsersSectionsSchema,
            )
        )

    class _UsersSectionsSchema(RequestsResponseSchema):
        """Schema for the "user's course sections" responses."""

        class _EnrollmentSchema(Schema):
            """Schema for extracting a section ID from an enrollment dict."""

            class Meta:
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

        return self._client.send(
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

        return self._client.send(
            "GET", f"files/{file_id}/public_url", schema=self._PublicURLSchema
        )["public_url"]

    class _PublicURLSchema(RequestsResponseSchema):
        """Schema for the public_url response."""

        public_url = fields.Str(required=True)

    @classmethod
    def _ensure_sections_unique(cls, sections):
        """
        Ensure that sections returned by Canvas are unique.

        We _suspect_ that Canvas may on occasion return the same section twice
        or more. In the case this happens, and the name is the same we remove
        the duplicates.

        :param sections: Sections to filter for duplicates
        :return: A list of unique sections
        :raise CanvasAPIError: When duplicate sections have different names
        """
        sections_by_id = {}

        for section in sections:
            duplicate = sections_by_id.get(section["id"])

            if duplicate and section.get("name") != duplicate.get("name"):
                raise CanvasAPIError(f"Duplicate section id on {section}")

            sections_by_id[section["id"]] = section

        return list(sections_by_id.values())
