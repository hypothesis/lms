from marshmallow import EXCLUDE, fields

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

        https://docs.valence.desire2learn.com/res/groups.html#post--d2l-api-lp-(version)-(orgUnitId)-groupcategories-(groupCategoryId)-groups-
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
