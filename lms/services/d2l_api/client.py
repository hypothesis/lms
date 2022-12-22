from typing import List

from marshmallow import EXCLUDE, Schema, fields

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
    def __init__(self, basic_client, request):
        self._api = basic_client
        self._request = request

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

    def list_files(self, org_unit) -> List[dict]:
        """Get a nested list of files and folders for the given `org_unit`."""

        modules = self._get_course_modules(org_unit)
        return list(self._find_files(modules))

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

    def _get_course_modules(self, org_unit) -> List[dict]:
        """
        Get a list of modules in the given course.

        https://docs.valence.desire2learn.com/res/content.html#get--d2l-api-le-(version)-(orgUnitId)-content-toc
        """
        response = self._api.request(
            "GET", self._api.api_url(f"/{org_unit}/content/toc", product="le")
        )
        return D2LTableOfContentsSchema(response).parse().get("modules", [])

    def _find_files(self, modules):
        """Recursively find files in modules."""
        for module in modules:
            module_files = [
                {
                    "type": "File",
                    "display_name": topic["display_name"],
                    "id": topic["id"],
                    "updated_at": topic["updated_at"],
                }
                for topic in module.get("topics", [])
                if topic.get("type") == "File"
            ]

            module_children = self._find_files(module.get("modules", []))
            yield {
                "type": "Folder",
                "display_name": module["display_name"],
                "id": module["id"],
                "updated_at": module["updated_at"],
                "children": module_files + list(module_children),
            }
