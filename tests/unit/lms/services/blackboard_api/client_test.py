from unittest.mock import MagicMock, Mock, call, create_autospec, sentinel

import pytest
from h_matchers import Any

from lms.services.blackboard_api._basic import BasicClient
from lms.services.blackboard_api.client import (
    PAGINATION_MAX_REQUESTS,
    BlackboardAPIClient,
)
from lms.services.exceptions import (
    ExternalAsyncRequestError,
    ExternalRequestError,
    FileNotFoundInCourse,
)
from tests import factories


class TestGetToken:
    def test_it(self, svc, basic_client):
        svc.get_token(sentinel.authorization_code)

        basic_client.get_token.assert_called_once_with(sentinel.authorization_code)


class TestRefreshAccessToken:
    def test_it(self, svc, basic_client):
        svc.refresh_access_token()

        basic_client.refresh_access_token.assert_called_once_with()


class TestListFiles:
    def test_it_returns_the_courses_top_level_contents(
        self,
        svc,
        basic_client,
        BlackboardListFilesSchema,
        blackboard_list_files_schema,
    ):
        basic_client.request.return_value = factories.requests.Response(json_data={})
        blackboard_files = [MagicMock() for _ in range(3)]
        blackboard_list_files_schema.parse.return_value = blackboard_files

        files = svc.list_files("COURSE_ID")

        basic_client.request.assert_called_once_with(
            "GET",
            Any.url.with_path("courses/uuid:COURSE_ID/resources").with_query(
                {
                    "limit": "200",
                    "fields": "id,name,type,modified,mimeType,size,parentId",
                }
            ),
        )

        BlackboardListFilesSchema.assert_called_once_with(
            basic_client.request.return_value
        )
        assert files == blackboard_list_files_schema.parse.return_value

    @pytest.mark.usefixtures("BlackboardListFilesSchema")
    def test_if_given_a_folder_id_it_returns_the_folders_contents(
        self,
        svc,
        basic_client,
    ):
        basic_client.request.return_value = factories.requests.Response(json_data={})

        svc.list_files("COURSE_ID", "FOLDER_ID")

        basic_client.request.assert_called_once_with(
            "GET",
            Any.url.with_path(
                "courses/uuid:COURSE_ID/resources/FOLDER_ID/children"
            ).with_query(
                {
                    "limit": "200",
                    "fields": "id,name,type,modified,mimeType,size,parentId",
                }
            ),
        )

    def test_it_with_pagination(self, svc, basic_client, blackboard_list_files_schema):
        # Each response from the Blackboard API includes the path to the next
        # page in the JSON body. This is the whole path to the next page,
        # including limit and offset query params, as a string. For example:
        # "/learn/api/public/v1/courses/uuid:<ID>/resources?limit=200&offset=200"  # noqa: ERA001
        #
        basic_client.request.side_effect = [
            factories.requests.Response(
                json_data={"paging": {"nextPage": "PAGE_2_PATH"}}
            ),
            factories.requests.Response(
                json_data={"paging": {"nextPage": "PAGE_3_PATH"}}
            ),
            factories.requests.Response(json_data={}),
        ]
        blackboard_files = [MagicMock() for _ in range(8)]

        # Each Blackboard API response contains a page of results.
        blackboard_list_files_schema.parse.side_effect = [
            blackboard_files[:3],
            blackboard_files[3:6],
            blackboard_files[6:],
        ]

        files = svc.list_files("COURSE_ID")

        # It called the Blackboard API three times getting the three pages.
        assert basic_client.request.call_args_list == [
            call(
                "GET",
                Any.url.with_path("courses/uuid:COURSE_ID/resources").with_query(
                    {
                        "limit": "200",
                        "fields": "id,name,type,modified,mimeType,size,parentId",
                    }
                ),
            ),
            call("GET", "PAGE_2_PATH"),
            call("GET", "PAGE_3_PATH"),
        ]
        # It returned all three pages of files as a single list.
        assert files == blackboard_files

    def test_it_doesnt_send_paginated_requests_forever(
        self, svc, basic_client, blackboard_list_files_schema
    ):
        # Make the Blackboard API send next page paths forever.
        basic_client.request.return_value = factories.requests.Response(
            json_data={"paging": {"nextPage": "NEXT_PAGE"}}
        )

        files = svc.list_files("COURSE_ID")

        assert basic_client.request.call_count == PAGINATION_MAX_REQUESTS
        assert len(files) == PAGINATION_MAX_REQUESTS * len(
            blackboard_list_files_schema.parse.return_value
        )

    @pytest.mark.parametrize("size,type_", [(1, "File"), (3, "File"), (3, "Folder")])
    def test_it_upserts_files(
        self,
        svc,
        basic_client,
        blackboard_list_files_schema,
        file_service,
        size,
        type_,
    ):
        basic_client.request.return_value = factories.requests.Response(json_data={})
        blackboard_list_files_schema.parse.return_value = [
            self.blackboard_file_dict(id_, type_=type_) for id_ in range(size)
        ]

        svc.list_files("COURSE_ID")

        file_service.upsert.assert_called_once_with(
            [
                Any.dict.containing(
                    {
                        "lms_id": id_ + 1,
                        "type": (
                            "blackboard_file"
                            if type_ == "File"
                            else "blackboard_folder"
                        ),
                    }
                )
                for id_ in range(size)
            ]
        )

    def blackboard_file_dict(self, id_=1, type_="File"):
        return {
            "type": type_,
            "course_id": "COURSE_ID",
            "id": id_ + 1,
            "name": f"file_entry_{id_}",
            "size": id_ * 2,
            "parentId": id_ * 4,
        }


class TestListAllFiles:
    def test_it(
        self,
        svc,
        basic_client,
        async_oauth_http_service,
        file_service,
        root_level_files,
        nested_files,
    ):
        basic_client.request.side_effect = [
            # Root level first page
            factories.requests.Response(
                json_data={
                    "results": root_level_files,
                    "paging": {"nextPage": "PAGE_2_PATH"},
                }
            ),
            # Root level second page is empty
            factories.requests.Response(json_data={"results": []}),
            # Subfolder second page is empty
            factories.requests.Response(json_data={"results": []}),
        ]
        async_oauth_http_service.request.side_effect = [
            [
                # First subfolder `FIRST PAGE FOLDER ID`
                factories.requests.Response(
                    json_data={
                        "results": nested_files,
                        "paging": {"nextPage": "SUBFOLDER_PAGE_2_PATH"},
                    }
                ),
            ],
            # Next level is empty
            [],
        ]

        files = svc.list_all_files("COURSE_ID")

        # Get we each page of the root level "folder"
        basic_client.request.assert_has_calls(
            [
                call(
                    # First call, gete root level elements
                    "GET",
                    Any.url.with_path("courses/uuid:COURSE_ID/resources").with_query(
                        {
                            "limit": "200",
                            "fields": "id,name,type,modified,mimeType,size,parentId",
                        }
                    ),
                ),
                # Get second page of the top level listing
                call("GET", "PAGE_2_PATH"),
            ]
        )
        basic_client._api_url.assert_any_call(  # noqa: SLF001
            "courses/uuid:COURSE_ID/resources/FIRST PAGE FOLDER ID/children?limit=200&fields=id%2Cname%2Ctype%2Cmodified%2CmimeType%2Csize%2CparentId"
        )

        async_oauth_http_service.request.assert_called_with(
            "GET",
            [basic_client._api_url.return_value],  # noqa: SLF001
        )
        # Get the pages of the subfolder
        basic_client.request.assert_called_with("GET", "SUBFOLDER_PAGE_2_PATH")
        basic_client._api_url.assert_called_with(  # noqa: SLF001
            "courses/uuid:COURSE_ID/resources/FIRST SUBFOLDER FOLDER ID/children?limit=200&fields=id%2Cname%2Ctype%2Cmodified%2CmimeType%2Csize%2CparentId"
        )

        assert files == root_level_files + nested_files
        # Files are stored in the DB
        file_service.upsert.assert_called_once()

    @pytest.fixture
    def root_level_files(self):
        return [
            # It contains one file
            {
                "id": "FIRST PAGE FILE ID",
                "name": "FIRST PAGE FILE NAME",
                "type": "File",
                "modified": "MODIFIED",
                "size": 100,
                "parentId": "PARENT",
            },
            # And one folder
            {
                "id": "FIRST PAGE FOLDER ID",
                "name": "FIRST PAGE FOLDER NAME",
                "type": "Folder",
                "modified": "MODIFIED",
                "size": 100,
                "parentId": "PARENT",
            },
        ]

    @pytest.fixture
    def nested_files(self):
        return [
            {
                "id": "FIRST SUBFOLDER FILE ID",
                "name": "FIRST SUBFOLDER FILE NAME",
                "type": "File",
                "modified": "MODIFIED",
                "size": 100,
                "parentId": "PARENT",
            },
            {
                "id": "FIRST SUBFOLDER FOLDER ID",
                "name": "FIRST SUBFOLDER FOLDER NAME",
                "type": "Folder",
                "modified": "MODIFIED",
                "size": 100,
                "parentId": "PARENT",
            },
        ]


class TestPublicURL:
    def test_it(
        self,
        svc,
        basic_client,
        BlackboardPublicURLSchema,
        blackboard_public_url_schema,
    ):
        public_url = svc.public_url("COURSE_ID", "FILE_ID")

        basic_client.request.assert_called_once_with(
            "GET", "courses/uuid:COURSE_ID/resources/FILE_ID?fields=downloadUrl"
        )
        BlackboardPublicURLSchema.assert_called_once_with(
            basic_client.request.return_value
        )
        assert public_url == blackboard_public_url_schema.parse.return_value

    def test_it_raises_FileNotFoundInCourse_if_the_Blackboard_API_404s(
        self, svc, basic_client
    ):
        basic_client.request.side_effect = ExternalRequestError(
            response=factories.requests.Response(status_code=404)
        )

        with pytest.raises(FileNotFoundInCourse) as excinfo:
            svc.public_url("COURSE_ID", "FILE_ID")

        assert excinfo.value.error_code == "blackboard_file_not_found_in_course"

    def test_it_raises_ExternalRequestError_if_the_Blackboard_API_fails_in_any_other_way(
        self, svc, basic_client
    ):
        basic_client.request.side_effect = ExternalRequestError(
            response=factories.requests.Response(status_code=400)
        )

        with pytest.raises(ExternalRequestError):
            svc.public_url("COURSE_ID", "FILE_ID")


class TestCourseGroupSets:
    def test_it(
        self,
        svc,
        basic_client,
        BlackboardListGroupSetsSchema,
        blackboard_list_groupsets_schema,
    ):
        group_sets = svc.course_group_sets("COURSE_ID")

        basic_client.request.assert_called_once_with(
            "GET", "/learn/api/public/v2/courses/uuid:COURSE_ID/groups/sets"
        )
        BlackboardListGroupSetsSchema.assert_called_once_with(
            basic_client.request.return_value
        )
        assert group_sets == blackboard_list_groupsets_schema.parse.return_value


class TestGroupSetGroups:
    def test_it(
        self,
        svc,
        basic_client,
        BlackboardListGroups,
        blackboard_list_groups,
    ):
        group_sets = svc.group_set_groups("COURSE_ID", "GROUP_SET_ID")

        basic_client.request.assert_called_once_with(
            "GET",
            "/learn/api/public/v2/courses/uuid:COURSE_ID/groups/sets/GROUP_SET_ID/groups",
        )
        BlackboardListGroups.assert_called_once_with(basic_client.request.return_value)
        assert group_sets == blackboard_list_groups.parse.return_value


class TestGroupCourseGroups:
    def test_it(
        self,
        svc,
        basic_client,
        BlackboardListGroups,
        blackboard_list_groups,
    ):
        groups = svc.course_groups("COURSE_ID", current_student_own_groups_only=False)

        basic_client.request.assert_called_once_with(
            "GET",
            "/learn/api/public/v2/courses/uuid:COURSE_ID/groups",
        )
        BlackboardListGroups.assert_called_once_with(basic_client.request.return_value)
        assert groups == blackboard_list_groups.parse.return_value

    def test_it_with_group_set_id(self, svc, blackboard_list_groups, groups):
        blackboard_list_groups.parse.return_value = groups

        groups = svc.course_groups(
            "COURSE_ID", "OTHER_GROUP_SET", current_student_own_groups_only=False
        )

        assert [group["groupSetId"] for group in groups] == ["OTHER_GROUP_SET"]

    def test_it_own_groups_all_instructor_only(
        self, svc, blackboard_list_groups, groups, async_oauth_http_service
    ):
        blackboard_list_groups.parse.return_value = groups

        groups = svc.course_groups(
            "COURSE_ID", "GROUP_SET", current_student_own_groups_only=True
        )

        assert [group["enrollment"]["type"] for group in groups] == ["InstructorOnly"]
        async_oauth_http_service.request.assert_not_called()

    def test_it_own_groups_all_self_enrollment(
        self, svc, blackboard_list_groups, groups, async_oauth_http_service
    ):
        blackboard_list_groups.parse.return_value = groups
        async_oauth_http_service.request.return_value = [Mock(status=200)]

        groups = svc.course_groups(
            "COURSE_ID", "OTHER_GROUP_SET", current_student_own_groups_only=True
        )

        assert len(groups) == 1
        assert groups[0]["enrollment"]["type"] == "SelfEnrollment"

    def test_it_own_groups_all_self_enrollment_no_groups(
        self, svc, blackboard_list_groups, groups, async_oauth_http_service
    ):
        blackboard_list_groups.parse.return_value = groups
        async_oauth_http_service.request.return_value = [Mock(status=403)]

        groups = svc.course_groups(
            "COURSE_ID", "OTHER_GROUP_SET", current_student_own_groups_only=True
        )

        assert not groups

    def test_it_own_groups(
        self, svc, blackboard_list_groups, groups, async_oauth_http_service
    ):
        blackboard_list_groups.parse.return_value = groups
        async_oauth_http_service.request.return_value = [Mock(status=200)]

        groups = svc.course_groups("COURSE_ID", current_student_own_groups_only=True)

        assert len(groups) == 2

    def test_it_request_error(
        self, svc, blackboard_list_groups, groups, async_oauth_http_service
    ):
        blackboard_list_groups.parse.return_value = groups
        async_oauth_http_service.request.return_value = [Mock(status=500)]

        with pytest.raises(ExternalAsyncRequestError):
            svc.course_groups("COURSE_ID", current_student_own_groups_only=True)

    @pytest.fixture
    def groups(self):
        return [
            {
                "id": "1",
                "name": "GROUP 1",
                "groupSetId": "OTHER_GROUP_SET",
                "enrollment": {"type": "SelfEnrollment"},
            },
            {
                "id": "2",
                "name": "GROUP 2",
                "groupSetId": "GROUP_SET",
                "enrollment": {"type": "InstructorOnly"},
            },
        ]


@pytest.fixture
def basic_client():
    return create_autospec(BasicClient, instance=True, spec_set=True)


@pytest.fixture
def svc(basic_client, pyramid_request, file_service):
    return BlackboardAPIClient(basic_client, pyramid_request, file_service)


@pytest.fixture
def BlackboardListFilesSchema(patch):
    return patch("lms.services.blackboard_api.client.BlackboardListFilesSchema")


@pytest.fixture
def blackboard_list_files_schema(BlackboardListFilesSchema):
    return BlackboardListFilesSchema.return_value


@pytest.fixture(autouse=True)
def BlackboardPublicURLSchema(patch):
    return patch("lms.services.blackboard_api.client.BlackboardPublicURLSchema")


@pytest.fixture
def blackboard_public_url_schema(BlackboardPublicURLSchema):
    return BlackboardPublicURLSchema.return_value


@pytest.fixture(autouse=True)
def BlackboardListGroupSetsSchema(patch):
    return patch("lms.services.blackboard_api.client.BlackboardListGroupSetsSchema")


@pytest.fixture
def blackboard_list_groupsets_schema(BlackboardListGroupSetsSchema):
    return BlackboardListGroupSetsSchema.return_value


@pytest.fixture
def blackboard_list_groups(BlackboardListGroups):
    return BlackboardListGroups.return_value


@pytest.fixture(autouse=True)
def BlackboardListGroups(patch):
    return patch("lms.services.blackboard_api.client.BlackboardListGroups")
