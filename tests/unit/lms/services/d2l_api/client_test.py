from unittest.mock import create_autospec, sentinel

import pytest

from lms.services.d2l_api._basic import BasicClient
from lms.services.d2l_api.client import D2LAPIClient


class TestD2LAPIClient:
    def test_get_token(self, svc, basic_client):
        svc.get_token(sentinel.authorization_code)

        basic_client.get_token.assert_called_once_with(sentinel.authorization_code)

    def test_refresh_access_token(self, svc, basic_client):
        svc.refresh_access_token()

        basic_client.refresh_access_token.assert_called_once_with()

    def test_course_group_sets(
        self, svc, basic_client, D2LGroupSetsSchema, d2l_group_sets_schema
    ):
        group_sets = svc.course_group_sets("COURSE_ID")

        basic_client.request.assert_called_once_with(
            "GET", "/COURSE_ID/groupcategories/"
        )
        D2LGroupSetsSchema.assert_called_once_with(basic_client.request.return_value)
        assert group_sets == d2l_group_sets_schema.parse.return_value

    def test_group_set_groups(
        self, svc, basic_client, D2LGroupsSchema, d2l_groups_schema, groups
    ):
        d2l_groups_schema.parse.return_value = groups

        response = svc.group_set_groups("COURSE_ID", "GROUP_SET")

        basic_client.request.assert_called_once_with(
            "GET", "/COURSE_ID/groupcategories/GROUP_SET/groups/"
        )
        D2LGroupsSchema.assert_called_once_with(basic_client.request.return_value)
        assert response == [dict(values, group_set_id="GROUP_SET") for values in groups]

    def test_group_set_groups_with_user_id(self, svc, d2l_groups_schema, groups):
        d2l_groups_schema.parse.return_value = groups

        response = svc.group_set_groups("COURSE_ID", "GROUP_SET", user_id=100)

        assert response == [
            dict(values, group_set_id="GROUP_SET")
            for values in groups
            if 100 in values["enrollments"]
        ]

    @pytest.mark.parametrize(
        "user_id,api_user_id",
        [
            ("shoolname_ID", "ID"),
            ("shoolname_prod_ID", "ID"),
            ("a72b0b30-5af8-4408-92a8-bffef472c4a7_ID", "ID"),
        ],
    )
    def test_get_api_user_id(self, svc, user_id, api_user_id):
        assert svc.get_api_user_id(user_id) == api_user_id

    @pytest.fixture
    def groups(self):
        return [
            {"id": 1, "name": "1", "enrollments": [100, 200]},
            {"id": 2, "name": "2", "enrollments": [200, 300]},
        ]

    @pytest.fixture(autouse=True)
    def D2LGroupSetsSchema(self, patch):
        return patch("lms.services.d2l_api.client.D2LGroupSetsSchema")

    @pytest.fixture
    def d2l_group_sets_schema(self, D2LGroupSetsSchema):
        return D2LGroupSetsSchema.return_value

    @pytest.fixture(autouse=True)
    def D2LGroupsSchema(self, patch):
        return patch("lms.services.d2l_api.client.D2LGroupsSchema")

    @pytest.fixture
    def d2l_groups_schema(self, D2LGroupsSchema):
        return D2LGroupsSchema.return_value

    @pytest.fixture
    def basic_client(self):
        return create_autospec(BasicClient, instance=True, spec_set=True)

    @pytest.fixture
    def svc(self, basic_client, pyramid_request):
        return D2LAPIClient(basic_client, pyramid_request)
