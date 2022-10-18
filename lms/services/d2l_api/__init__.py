from lms.services.exceptions import ExternalRequestError, OAuth2TokenError
from urllib.parse import urlencode
from lms.services.aes import AESService


class BasicClient:
    def __init__(
        self,
        oauth_http_service,
        http_service,
        lms_host,
        client_id,
        client_secret,
        redirect_uri,
    ):
        self._http_service = http_service
        self._oauth_http_service = oauth_http_service

        self.lms_host = "aunltd.brightspacedemo.com"
        self.token_url = "https://auth.brightspace.com/core/connect/token"
        self.client_id = client_id
        self.client_secret = client_secret

        self.redirect_uri = "https://localhost:48001/api/d2l/oauth/callback"

        # https://docs.valence.desire2learn.com/basic/oauth2.html

        # Authorization endpoint: https://auth.brightspace.com/oauth2/auth
        # Token endpoint: https://auth.brightspace.com/core/connect/token

        self.api_version = "1.31"

    def get_token(self, authorization_code):
        self._oauth_http_service.get_access_token(
            token_url=self.token_url,
            redirect_uri=self.redirect_uri,
            auth=(self.client_id, self.client_secret),
            authorization_code=authorization_code,
        )

    def refresh_access_token(self):
        self._oauth_http_service.refresh_access_token(
            self.token_url,
            self.redirect_uri,
            auth=(self.client_id, self.client_secret),
        )

    def request(self, method, path, **kwargs):
        if path.startswith("/"):
            path = self.api_url(path)

        try:
            return self._oauth_http_service.request(method, path, **kwargs)
        except ExternalRequestError as err:
            err.refreshable = getattr(err.response, "status_code", None) == 401
            raise

    def api_url(self, path, product="lp"):
        return f"https://{self.lms_host}/d2l/api/{product}/{self.api_version}{path}"


from marshmallow import EXCLUDE, Schema, fields, post_load

from lms.validation._base import RequestsResponseSchema


class GroupSetSchema(RequestsResponseSchema):
    """
    [{"GroupCategoryId":22,"EnrollmentStyle":"PeoplePerGroupAutoEnrollment","EnrollmentQuantity":2,"AutoEnroll":false,"RandomizeEnrollments":true,"Name":"Group Category testing","Description":{"Text":"","Html":""},"Groups":[6793],"MaxUsersPerGroup":2,"RestrictedByOrgUnitId":null}]
    """

    many = True

    class Meta:
        unknown = EXCLUDE

    id = fields.Int(required=True, data_key="GroupCategoryId")
    name = fields.Str(required=True, data_key="Name")


class GroupSchema(RequestsResponseSchema):
    """
    [{"GroupId":6793,"Name":"Test Group 1","Code":"Test Group_6782_1","Description":{"Text":"","Html":""},"Enrollments":[355]}]
    """

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
        Save a new Blackboard access token for the current user to the DB.

        :raise services.ExternalRequestError: if something goes wrong with the
            access token request to Blackboard
        """
        self._api.get_token(authorization_code)

    def refresh_access_token(self):
        """
        Refresh the current user's access token in the DB.

        :raise services.ExternalRequestError: if something goes wrong with the
            refresh token request to Blackboard
        """
        self._api.refresh_access_token()

    def course_group_sets(self, ou):
        response = self._api.request(
            "GET",
            f"/{ou}/groupcategories/",
        )

        return GroupSetSchema(response).parse()

    def group_set_groups(self, ou, group_category_id, user_id=None):
        response = self._api.request(
            "GET",
            f"/{ou}/groupcategories/{group_category_id}/groups/",
        )
        groups = GroupSchema(response).parse()
        # D2L doesn't return the group_set_id of the listed groups as other LMS
        # but we know which one it is because we queried for it, inject it:
        groups = [dict(group, group_set_id=group_category_id) for group in groups]

        if user_id:
            groups = [group for group in groups if int(user_id) in group["enrollments"]]

        return groups

    def course_table_of_contents(self, ou):
        response = self._api.request(
            "GET", self._api.api_url(f"/{ou}/content/toc", product="le")
        )
        return response

    def public_url(self, ou, file_path):
        query = {"path": file_path}
        # response = self._api.request(
        #    "GET",
        #    # self._api.api_url(f"/{ou}/managefiles/file?{urlencode(query)}"),
        #    self._api.api_url(f"/{ou}/managefiles/file?path={file_path}"),
        #    allow_redirects=False,  # No luck, no redirect
        # )
        # print(response)
        # Maybe try: https://docs.valence.desire2learn.com/res/content.html#get--d2l-api-le-(version)-(orgUnitId)-content-topics-(topicId)-file
        return self._api.api_url(f"/{ou}/managefiles/file?path={file_path}")


def factory(_context, request):
    application_instance = request.find_service(
        name="application_instance"
    ).get_current()

    client_secret = application_instance.decrypted_developer_secret(
        request.find_service(AESService)
    )

    return D2LAPIClient(
        BasicClient(
            lms_host=application_instance.lms_host(),
            client_id=application_instance.developer_key,
            client_secret=client_secret,
            redirect_uri=request.route_url("d2l_api.oauth.callback"),
            http_service=request.find_service(name="http"),
            oauth_http_service=request.find_service(name="oauth_http"),
        ),
        request=request,
    )
