from unittest.mock import create_autospec, sentinel

import pytest

from lms.services.d2l_api._basic import BasicClient
from lms.services.d2l_api.client import D2LAPIClient
from lms.services.exceptions import ExternalRequestError, FileNotFoundInCourse
from tests import factories


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
        "modules,files,db_files",
        [
            (
                {
                    "Modules": [
                        {
                            "ModuleId": 1,
                            "LastModifiedDate": "DATE 1",
                            "Title": "MODULE 1",
                            "Topics": [
                                {
                                    "Identifier": "FILE 1",
                                    "TypeIdentifier": "File",
                                    "Title": "TITLE 1",
                                    "LastModifiedDate": "DATE 1",
                                    "Url": "TITLE 1.pdf",
                                },
                                # Check we don't include non-files
                                {
                                    "Identifier": "ID 2",
                                    "TypeIdentifier": "NOT A FILE",
                                    "Title": "NAME 2",
                                    "LastModifiedDate": "DATE 2",
                                    "Url": "NAME 2.pdf",
                                },
                                # Check we don't include non-pdfs
                                {
                                    "Identifier": "ID 2",
                                    "TypeIdentifier": "NOT A PDF",
                                    "Title": "NOT PDF",
                                    "LastModifiedDate": "DATE 2",
                                    "Url": "NOT PDF.png",
                                },
                                # Check we don't include broken links
                                {
                                    "Identifier": "BROKEN",
                                    "IsBroken": True,
                                    "TypeIdentifier": "BROKEN",
                                    "Title": "BROKEN",
                                    "LastModifiedDate": "DATE 2",
                                    # Broken topics don't have URLs
                                    "Url": None,
                                },
                            ],
                            "Modules": [
                                {
                                    "ModuleId": 2,
                                    "LastModifiedDate": "DATE 2",
                                    "Title": "MODULE 2",
                                    "Topics": [
                                        {
                                            "Identifier": "FILE 2",
                                            "TypeIdentifier": "File",
                                            "Title": "TITLE 2",
                                            "LastModifiedDate": "DATE 2",
                                            "Url": "FILE 2.pdf",
                                        }
                                    ],
                                }
                            ],
                        }
                    ]
                },
                [
                    {
                        "display_name": "MODULE 1",
                        "id": 1,
                        "lms_id": 1,
                        "updated_at": "DATE 1",
                        "type": "Folder",
                        "children": [
                            {
                                "display_name": "TITLE 1",
                                "id": "d2l://file/course/COURSE_ID/file_id/FILE 1/",
                                "lms_id": "FILE 1",
                                "type": "File",
                                "updated_at": "DATE 1",
                                "mime_type": "application/pdf",
                            },
                            {
                                "display_name": "MODULE 2",
                                "id": 2,
                                "lms_id": 2,
                                "type": "Folder",
                                "updated_at": "DATE 2",
                                "children": [
                                    {
                                        "display_name": "TITLE 2",
                                        "id": "d2l://file/course/COURSE_ID/file_id/FILE 2/",
                                        "lms_id": "FILE 2",
                                        "type": "File",
                                        "updated_at": "DATE 2",
                                        "mime_type": "application/pdf",
                                    },
                                ],
                            },
                        ],
                    },
                ],
                [
                    {
                        "type": "d2l_folder",
                        "course_id": "COURSE_ID",
                        "lms_id": 1,
                        "name": "MODULE 1",
                        "parent_lms_id": None,
                    },
                    {
                        "type": "d2l_file",
                        "course_id": "COURSE_ID",
                        "lms_id": "FILE 1",
                        "name": "TITLE 1",
                        "parent_lms_id": 1,
                    },
                    {
                        "type": "d2l_folder",
                        "course_id": "COURSE_ID",
                        "lms_id": 2,
                        "name": "MODULE 2",
                        "parent_lms_id": 1,
                    },
                    {
                        "type": "d2l_file",
                        "course_id": "COURSE_ID",
                        "lms_id": "FILE 2",
                        "name": "TITLE 2",
                        "parent_lms_id": 2,
                    },
                ],
            ),
        ],
    )
    def test_list_files(
        self, svc, basic_client, modules, files, db_files, file_service
    ):
        basic_client.request.return_value.json.return_value = modules

        returned_files = svc.list_files("COURSE_ID")

        basic_client.api_url.assert_called_once_with(
            "/COURSE_ID/content/toc", product="le"
        )
        basic_client.request.assert_called_once_with(
            "GET", basic_client.api_url.return_value
        )

        file_service.upsert.assert_called_with(db_files)

        assert files == returned_files

    @pytest.mark.parametrize(
        "modules",
        [
            {
                "Modules": [
                    {
                        "ModuleId": 1,
                        "LastModifiedDate": "DATE 1",
                        "Title": "MODULE 1",
                        "Topics": [
                            # Non-broken files without URL
                            {
                                "Identifier": "BROKEN",
                                "IsBroken": False,
                                "TypeIdentifier": "BROKEN",
                                "Title": "BROKEN",
                                "LastModifiedDate": "DATE 2",
                                "Url": None,
                            },
                        ],
                    }
                ]
            },
        ],
    )
    def test_list_files_raises_for_invalid_data(self, svc, basic_client, modules):
        basic_client.request.return_value.json.return_value = modules

        with pytest.raises(ExternalRequestError):
            svc.list_files("COURSE_ID")

    def test_public_url(self, svc, basic_client):
        public_url = svc.public_url("COURSE_ID", "FILE_ID")

        basic_client.api_url.assert_any_call(
            "/COURSE_ID/content/topics/FILE_ID", product="le"
        )
        basic_client.request.assert_called_once_with(
            "GET", basic_client.api_url.return_value
        )

        basic_client.api_url.assert_called_with(
            "/COURSE_ID/content/topics/FILE_ID/file?stream=1", product="le"
        )

        assert public_url == basic_client.api_url.return_value

    @pytest.mark.parametrize(
        "status_code,user_fixture_name,exception,error_code",
        [
            (
                404,
                "user_is_learner",
                FileNotFoundInCourse,
                "d2l_file_not_found_in_course_student",
            ),
            (
                404,
                "user_is_instructor",
                FileNotFoundInCourse,
                "d2l_file_not_found_in_course_instructor",
            ),
            (400, "user_is_learner", ExternalRequestError, None),
        ],
    )
    def test_public_url_raises(
        self,
        svc,
        basic_client,
        status_code,
        user_fixture_name,
        exception,
        error_code,
        request,
    ):
        _ = request.getfixturevalue(user_fixture_name)
        basic_client.request.side_effect = ExternalRequestError(
            response=factories.requests.Response(status_code=status_code)
        )

        with pytest.raises(exception) as excinfo:
            svc.public_url("COURSE_ID", "FILE_ID")

        if error_code:
            assert excinfo.value.error_code == error_code

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
    def svc(self, basic_client, file_service, lti_user):
        return D2LAPIClient(basic_client, file_service, lti_user)
