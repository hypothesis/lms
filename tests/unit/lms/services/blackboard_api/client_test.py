from unittest.mock import MagicMock, call, create_autospec, sentinel

import pytest
from h_matchers import Any

from lms.events import FilesDiscoveredEvent
from pyramid.registry import Registry
from lms.services.blackboard_api._basic import BasicClient
from lms.services.blackboard_api.client import (
    PAGINATION_MAX_REQUESTS,
    BlackboardAPIClient,
)
from lms.services.exceptions import BlackboardFileNotFoundInCourse, HTTPError
from tests import factories


class TestGetToken:
    def test_it(self, svc, basic_client):
        svc.get_token(sentinel.authorization_code)

        basic_client.get_token.assert_called_once_with(sentinel.authorization_code)


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
        # "/learn/api/public/v1/courses/uuid:<ID>/resources?limit=200&offset=200"
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

    def test_it_raises_BlackboardFileNotFoundInCourse_if_the_Blackboard_API_404s(
        self, svc, basic_client
    ):
        basic_client.request.side_effect = HTTPError(
            factories.requests.Response(status_code=404)
        )

        with pytest.raises(BlackboardFileNotFoundInCourse):
            svc.public_url("COURSE_ID", "FILE_ID")

    def test_it_raises_HTTPError_if_the_Blackboard_API_fails_in_any_other_way(
        self, svc, basic_client
    ):
        basic_client.request.side_effect = HTTPError(
            factories.requests.Response(status_code=400)
        )

        with pytest.raises(HTTPError):
            svc.public_url("COURSE_ID", "FILE_ID")


@pytest.fixture
def basic_client():
    return create_autospec(BasicClient, instance=True, spec_set=True)


@pytest.fixture
def svc(basic_client, pyramid_request):
    return BlackboardAPIClient(basic_client, pyramid_request)


@pytest.fixture(autouse=True)
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
