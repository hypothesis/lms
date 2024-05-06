from marshmallow import EXCLUDE, Schema, ValidationError, fields, validates_schema

from lms.services.exceptions import ExternalRequestError, FileNotFoundInCourse
from lms.validation._base import RequestsResponseSchema


class D2LGroupSetsSchema(RequestsResponseSchema):
    many = True

    class Meta:
        unknown = EXCLUDE

    id = fields.Int(required=True, data_key="GroupCategoryId")
    name = fields.Str(required=True, data_key="Name")


class D2LGroupsSchema(RequestsResponseSchema):
    many = True

    class Meta:
        unknown = EXCLUDE

    id = fields.Int(required=True, data_key="GroupId")
    name = fields.Str(required=True, data_key="Name")
    group_set_id = fields.Int(required=False)
    enrollments = fields.List(fields.Int(), required=True, data_key="Enrollments")


class _D2LTopic(Schema):
    """Files and assigmetns are topics within a module."""

    class Meta:
        unknown = EXCLUDE

    id = fields.Str(required=True, data_key="Identifier")
    display_name = fields.Str(required=True, data_key="Title")
    updated_at = fields.Str(required=True, data_key="LastModifiedDate")
    type = fields.Str(required=True, data_key="TypeIdentifier")
    is_broken = fields.Boolean(data_key="IsBroken")
    url = fields.Str(required=False, allow_none=True, data_key="Url")
    """Url contains the full filename, useful to get the extension of the file"""

    @validates_schema
    def validate_url(self, data, **_kwargs):
        if not data.get("is_broken", False) and not data.get("url"):
            raise ValidationError("URL is required for topics", "url")


class _D2LModuleSchema(Schema):
    """D2L course sections are called "modules". They can contain nested sub-modules."""

    class Meta:
        unknown = EXCLUDE

    id = fields.Int(required=True, data_key="ModuleId")
    display_name = fields.Str(required=True, data_key="Title")
    updated_at = fields.Str(required=True, data_key="LastModifiedDate")
    modules = fields.List(
        fields.Nested(lambda: _D2LModuleSchema), required=False, data_key="Modules"
    )
    topics = fields.List(fields.Nested(_D2LTopic), required=False, data_key="Topics")


class D2LTableOfContentsSchema(RequestsResponseSchema):
    modules = fields.List(
        fields.Nested(_D2LModuleSchema), required=True, data_key="Modules"
    )


class D2LAPIClient:
    def __init__(self, basic_client, file_service, lti_user):
        self._api = basic_client
        self._file_service = file_service
        self._lti_user = lti_user

    def get_token(self, authorization_code):
        """
        Save a new access token for the current user to the DB.

        :raise services.ExternalRequestError: if something goes wrong with the
            access token request
        """
        self._api.get_token(authorization_code)

    def refresh_access_token(self):
        """
        Refresh the current user's access token in the DB.

        :raise services.ExternalRequestError: if something goes wrong with the
            refresh token request
        """
        self._api.refresh_access_token()

    def course_group_sets(self, org_unit):
        """
        Get the group categories of an org unit.

        https://docs.valence.desire2learn.com/res/groups.html#get--d2l-api-lp-(version)-(orgUnitId)-groupcategories-
        """
        response = self._api.request("GET", f"/{org_unit}/groupcategories/")
        return D2LGroupSetsSchema(response).parse()

    def group_set_groups(self, org_unit, group_category_id, user_id=None):
        """
        Get the groups in a group category.

        https://docs.valence.desire2learn.com/res/groups.html#get--d2l-api-lp-(version)-(orgUnitId)-groupcategories-(groupCategoryId)-groups-
        """
        response = self._api.request(
            "GET",
            f"/{org_unit}/groupcategories/{group_category_id}/groups/",
        )
        groups = D2LGroupsSchema(response).parse()
        # D2L doesn't return the group_set_id of the listed groups as other LMS
        # but we know which one it is because we queried for it, inject it:
        for group in groups:
            group["group_set_id"] = group_category_id

        if user_id:
            groups = [group for group in groups if int(user_id) in group["enrollments"]]

        return groups

    def list_files(self, org_unit) -> list[dict]:
        """Get a nested list of files and folders for the given `org_unit`."""
        modules = self._get_course_modules(org_unit)
        files = list(self._find_files(org_unit, modules))
        self._file_service.upsert(list(self._files_for_storage(org_unit, files)))

        return files

    def public_url(self, org_unit, file_id) -> str:
        """
        Return the URL to download the given file.

        As opposed to other LMS's that return a one time signed URL that we can then pass along to Via
        D2L requires us to send the API authentication header to get the file contents.

        To make sure the API authentication header is not expired we'll make a API
        request here so if it needs to be refreshed we follow the standard token refresh procedure.

        https://docs.valence.desire2learn.com/res/content.html#get--d2l-api-le-(version)-(orgUnitId)-content-topics-(topicId)
        https://docs.valence.desire2learn.com/res/content.html#get--d2l-api-le-(version)-(orgUnitId)-content-topics-(topicId)-file
        """
        try:
            # We don't need the data from this call.
            # We are only interested on the potential side effect of needing
            # a new access token and/or refreshing an existing one
            # or finding out that the file is not present anymore.
            self._api.request(
                "GET",
                self._api.api_url(
                    f"/{org_unit}/content/topics/{file_id}", product="le"
                ),
            )
        except ExternalRequestError as err:
            if err.status_code == 404:
                raise FileNotFoundInCourse(
                    (
                        "d2l_file_not_found_in_course_instructor"
                        if self._lti_user.is_instructor
                        else "d2l_file_not_found_in_course_student"
                    ),
                    file_id,
                ) from err
            raise

        return self._api.api_url(
            f"/{org_unit}/content/topics/{file_id}/file?stream=1", product="le"
        )

    @staticmethod
    def get_api_user_id(user_id: str):
        """
        Get the user id to use with the API from the LTI user_id.

        D2L user_id seem to follow two schemas:

        LONG-UUID-HEX_ID
        shorthumanreadablename_ID

        Note that in the second type we've seen names that include "_"
        so we don't take the second part of the string but the last.
        """
        return user_id.split("_")[-1]

    def _get_course_modules(self, org_unit) -> list[dict]:
        """
        Get a list of modules in the given course.

        https://docs.valence.desire2learn.com/res/content.html#get--d2l-api-le-(version)-(orgUnitId)-content-toc
        """
        response = self._api.request(
            "GET", self._api.api_url(f"/{org_unit}/content/toc", product="le")
        )
        return D2LTableOfContentsSchema(response).parse().get("modules", [])

    def _find_files(self, course_id, modules):
        """Recursively find files in modules."""
        for module in modules:
            module_files = [
                {
                    "type": "File",
                    "mime_type": "application/pdf",
                    "display_name": topic["display_name"],
                    "lms_id": topic["id"],
                    "id": f"d2l://file/course/{course_id}/file_id/{topic['id']}/",
                    "updated_at": topic["updated_at"],
                }
                for topic in module.get("topics", [])
                if topic.get("type") == "File"
                and not topic.get("is_broken", False)
                # Filter out non-pdfs using the file's name.
                # Other LMS offer the content type of the file at this level
                # but will have to rely on the extension for D2L.
                and topic["url"].lower().endswith(".pdf")
            ]

            module_children = self._find_files(course_id, module.get("modules", []))
            yield {
                "type": "Folder",
                "display_name": module["display_name"],
                "id": module["id"],
                "lms_id": module["id"],
                "updated_at": module["updated_at"],
                "children": module_files + list(module_children),
            }

    def _files_for_storage(self, course_id, files, parent_id=None):
        for file in files:
            yield {
                "type": "d2l_file" if file["type"] == "File" else "d2l_folder",
                "course_id": course_id,
                "lms_id": file["lms_id"],
                "name": file["display_name"],
                "parent_lms_id": parent_id,
            }

            yield from self._files_for_storage(
                course_id, file.get("children", []), file["id"]
            )
