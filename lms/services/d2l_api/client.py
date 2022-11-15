from marshmallow import EXCLUDE, fields

from lms.validation._base import RequestsResponseSchema


class D2LGroupSetsSchema(RequestsResponseSchema):
    many = True

    class Meta:
        unknown = EXCLUDE

    id = fields.Int(required=True, data_key="GroupCategoryId")
    name = fields.Str(required=True, data_key="Name")


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

    def course_group_sets(self, ou):
        """
        Get the group categories of an org unit (OU).

        https://docs.valence.desire2learn.com/res/groups.html#get--d2l-api-lp-(version)-(orgUnitId)-groupcategories-
        """
        response = self._api.request("GET", f"/{ou}/groupcategories/")
        return D2LGroupSetsSchema(response).parse()
