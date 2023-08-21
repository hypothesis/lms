"""High level access to Canvas API methods."""

import logging
from collections import defaultdict
from functools import lru_cache

import marshmallow
from marshmallow import EXCLUDE, Schema, fields, post_load, validate, validates_schema

from lms.services.canvas_api._pages import CanvasPagesClient
from lms.services.exceptions import CanvasAPIError
from lms.services.file import FileService
from lms.validation import RequestsResponseSchema

log = logging.getLogger(__name__)


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

    :raise OAuth2TokenError: if we can't get the list of sections because we
        don't have a working Canvas API access token for the user
    :raise CanvasAPIServerError: if we do have an access token but the
        Canvas API request fails for any other reason
    """

    def __init__(
        self,
        authenticated_client,
        file_service: FileService,
        pages_client: CanvasPagesClient,
        folders_enabled: bool = False,
    ):
        """
        Create a new CanvasAPIClient.

        :param authenticated_client: An instance of AuthenticatedClient
        :param file_service: FileService for persisting files from the API to the DB
        :param folders_enabled: Whether to use folders while listing files
        """
        self._client = authenticated_client
        self._file_service = file_service
        self._folders_enabled = folders_enabled

        self._pages = pages_client

    @property
    def pages(self):
        """Expose the Pages client."""
        return self._pages

    def get_token(self, authorization_code):
        """
        Get an access token for the current LTI user.

        :param authorization_code: The Canvas API OAuth 2.0 authorization code
            to exchange for an access token
        :return: An access token string
        """
        return self._client.get_token(authorization_code)

    def get_refreshed_token(self, refresh_token):
        return self._client.get_refreshed_token(refresh_token)

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
        def post_load(self, data, **_kwargs):
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
        def _validate_length(self, data, **_kwargs):
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
        def post_load(self, data, **_kwargs):
            # Return a list of section ids in the same style as the course
            # sections (but without names).

            return [
                {"id": enrollment["course_section_id"]}
                for enrollment in data["enrollments"]
            ]

    @lru_cache(maxsize=128)
    def list_files(self, course_id, sort="position") -> list[dict]:
        """
        Return the list of files for the given `course_id`.

        :param course_id: the Canvas course_id of the course to look in
        :param sort: field to sort by (on Canvas' API side).
            Defaults to "position" which is an undocumented option but that it should be the most stable of the options available as it sorts by both "position" and "name" on Canvas' side.
            https://github.com/instructure/canvas-lms/blob/d43feb92d40d2c69684c4536f74dec37992c557a/app/controllers/files_controller.rb#L305
        """
        # For documentation of this request see:
        # https://canvas.instructure.com/doc/api/files.html#method.files.api_index

        files = self._client.send(
            "GET",
            f"courses/{course_id}/files",
            params={"content_types[]": "application/pdf", "sort": sort},
            schema=self._ListFilesSchema,
        )
        # Canvas' pagination is broken as it sorts by fields that allows duplicates.
        # This can lead to objects being skipped or duplicated across pages.
        # We can't detected objects that are not returned but we can detect the duplicates,
        #   remove them and notify sentry to see how often this happens after using a different sort parameter.
        raw_count = len(files)
        files = list(
            {file_["id"]: file_ for file_ in files}.values()
        )  # De_duplicate by ID
        de_duplicated_count = len(files)
        if raw_count != de_duplicated_count:
            log.exception(
                "Duplicates files found in Canvas courses/{course_id}/files endpoint"
            )

        self._file_service.upsert(
            [
                {
                    "type": "canvas_file",
                    "course_id": course_id,
                    "lms_id": file["id"],
                    "name": file["display_name"],
                    "size": file["size"],
                    "parent_lms_id": file["folder_id"],
                }
                for file in files
            ]
        )

        if self._folders_enabled:
            folders = self._list_folders(course_id)

            # Organize every item (file and folders) by its parent ID
            items_by_parent = defaultdict(list)
            for file in files:
                items_by_parent[file["folder_id"]].append(dict(file, type="File"))
            for folder in folders:
                items_by_parent[folder["folder_id"]].append(dict(folder, type="Folder"))

            # Find the root folder, the one with a None parent
            root_folder_id = [f for f in folders if not f["folder_id"]][0]["id"]

            return sorted(
                self._files_tree(items_by_parent, folder_id=root_folder_id),
                key=lambda item: item["display_name"].lower(),
            )

        return sorted(files, key=lambda file_: file_["display_name"])

    def _list_folders(self, course_id):
        """Get all folders of a given course_id."""
        folders = self._client.send(
            "GET", f"courses/{course_id}/folders", schema=self._ListFoldersSchema
        )
        # Store the folders in the DB
        self._file_service.upsert(
            [
                {
                    "type": "canvas_folder",
                    "course_id": course_id,
                    "lms_id": folder["id"],
                    "name": folder["display_name"],
                    "parent_lms_id": folder["folder_id"],
                }
                for folder in folders
            ]
        )
        return folders

    def _files_tree(self, items: dict[int, list], folder_id: int):
        """Build a tree of files/folders recursively."""
        for item in items[folder_id]:
            if item["type"] == "Folder":
                # For folders, recursively attach children
                yield dict(
                    item,
                    children=sorted(
                        self._files_tree(items, folder_id=item["id"]),
                        key=lambda item: item["display_name"],
                    ),
                )
            else:
                # For files, yield them
                yield item

    class _ListFilesSchema(RequestsResponseSchema):
        """Schema for the files returned by Canvas' API."""

        many = True

        display_name = fields.Str(required=True)
        id = fields.Integer(required=True)
        updated_at = fields.String(required=True)
        size = fields.Integer(required=True)
        folder_id = fields.Integer(required=True)

    class _ListFoldersSchema(RequestsResponseSchema):
        """Schema for the folders returned by Canvas' API."""

        many = True

        display_name = fields.Str(required=True, data_key="name")
        folder_id = fields.Integer(
            required=True, allow_none=True, data_key="parent_folder_id"
        )
        id = fields.Integer(required=True)
        updated_at = fields.String(required=True)

    @lru_cache(maxsize=128)
    def public_url(self, file_id):
        """
        Get a new temporary public download URL for the file with the given ID.

        :param file_id: the ID of the Canvas file
        """
        # For documentation of this request see:
        # https://canvas.instructure.com/doc/api/files.html#method.files.public_url

        return self._client.send(
            "GET", f"files/{file_id}/public_url", schema=self._PublicURLSchema
        )["public_url"]

    class _PublicURLSchema(RequestsResponseSchema):
        """Schema for the public_url response."""

        public_url = fields.Str(required=True)

    def course_group_categories(self, course_id):
        return self._client.send(
            "GET",
            f"courses/{course_id}/group_categories",
            schema=self._ListGroupCategories,
        )

    class _ListGroupCategories(RequestsResponseSchema):
        many = True

        id = fields.Integer(required=True)
        name = fields.Str(required=True)

    def group_category_groups(self, course_id, group_category_id):
        """
        List groups that belong to the group category/group set `group_category_id`.

        :param course_id: the ID of the course that the group set should belong to
        :param group_category_id: the ID of the group set
        :raise CanvasAPIError: if the group set `group_category_id` is not found
        or is not in the course `course_id`
        (for example the group set might belong to a different course,
        or it might have been deleted)
        """
        groups = self._client.send(
            "GET",
            f"group_categories/{group_category_id}/groups",
            schema=self._ListGroups,
        )
        # The response might include groups from a course other than the current one.
        # This is most likely due to course copy, the groups are from the original course.
        if any((group["course_id"]) != int(course_id) for group in groups):
            # The group set is not in the given course.
            # For example this could be because the course was copied (assignments in copied
            # courses still have the group set IDs from the original course)
            raise CanvasAPIError(
                f"Group set {group_category_id} doesn't belong to course {course_id}"
            )

        return groups

    def course_groups(self, course_id, only_own_groups=True, include_users=False):
        """
        Get all the groups of a course.

        :param course_id: Course canvas ID
        :param only_own_groups: Only return groups the current users belongs to
        :param include_users: Optionally include all the users in each group
        """
        params = {"only_own_groups": only_own_groups}
        send_kwargs = {}

        if include_users:
            params["include[]"] = "users"

            # It looks like Canvas's course groups API may sometimes be very
            # slow when called with ?include[]=users (possibly for courses that
            # have many users) so use a larger timeout for these particular
            # requests.
            send_kwargs["timeout"] = (31, 31)

        return self._client.send(
            "GET",
            f"courses/{course_id}/groups",
            params=params,
            schema=self._ListGroups,
            **send_kwargs,
        )

    def current_user_groups(self, course_id, group_category_id=None):
        """
        Get all groups the current user belongs in a course and optionally in a group_category.

        :param course_id: Course canvas ID
        :param group_category_id: Only return groups that belong to this group category
        """
        user_groups = self.course_groups(course_id, only_own_groups=True)

        if group_category_id:
            user_groups = [
                g
                for g in user_groups
                if g["group_category_id"] == int(group_category_id)
            ]

        return user_groups

    def user_groups(self, course_id, user_id, group_category_id=None):
        """
        Get the groups a `user_id` belongs to in an specific `course_id`.

        Optionally return only the groups that belong to a `group_category_id`
        """
        canvas_groups = self.course_groups(
            course_id, only_own_groups=False, include_users=True
        )
        groups = []
        # Look for the student we are grading in all the groups
        for group in canvas_groups:
            if group_category_id and group["group_category_id"] != int(
                group_category_id
            ):
                continue

            for user in group.get("users", []):
                if user["id"] == int(user_id):
                    groups.append(group)

        return groups

    class _ListGroups(RequestsResponseSchema):
        class _Users(Schema):
            """Users that belong to each group. Only present when using include[]=users."""

            class Meta:
                unknown = EXCLUDE

            id = fields.Integer(required=True)

        users = fields.List(
            fields.Nested(_Users),
            required=False,
        )

        many = True
        id = fields.Integer(required=True)
        name = fields.Str(required=True)
        description = fields.String(load_default=None, allow_none=True)
        group_category_id = fields.Integer(required=True)
        course_id = fields.Integer(required=True)

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
