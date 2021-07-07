from unittest.mock import call, sentinel

import pytest

from lms.services.blackboard_api.client import (
    PAGINATION_MAX_REQUESTS,
    BlackboardAPIClient,
)
from lms.services.exceptions import BlackboardFileNotFoundInCourse, HTTPError
from tests import factories


class TestListFiles:
    def test_it(
        self,
        svc,
        basic_blackboard_api_client,
        BlackboardListFilesSchema,
        blackboard_list_files_schema,
    ):
        basic_blackboard_api_client.request.return_value = factories.requests.Response(
            json_data={}
        )
        blackboard_list_files_schema.parse.return_value = [
            sentinel.file_1,
            sentinel.file_2,
            sentinel.file_3,
        ]

        files = svc.list_files("COURSE_ID")

        basic_blackboard_api_client.request.assert_called_once_with(
            "GET", "courses/uuid:COURSE_ID/resources?type=file&limit=200"
        )
        BlackboardListFilesSchema.assert_called_once_with(
            basic_blackboard_api_client.request.return_value
        )
        assert files == blackboard_list_files_schema.parse.return_value

    def test_it_with_pagination(
        self, svc, basic_blackboard_api_client, blackboard_list_files_schema
    ):
        # Each response from the Blackboard API includes the path to the next
        # page in the JSON body. This is the whole path to the next page,
        # including limit and offset query params, as a string. For example:
        # "/learn/api/public/v1/courses/uuid:<ID>/resources?limit=200&offset=200"
        #
        basic_blackboard_api_client.request.side_effect = [
            factories.requests.Response(
                json_data={"paging": {"nextPage": "PAGE_2_PATH"}}
            ),
            factories.requests.Response(
                json_data={"paging": {"nextPage": "PAGE_3_PATH"}}
            ),
            factories.requests.Response(json_data={}),
        ]

        # Each Blackboard API response contains a page of results.
        blackboard_list_files_schema.parse.side_effect = [
            [sentinel.file_1, sentinel.file_2, sentinel.file_3],
            [sentinel.file_4, sentinel.file_5, sentinel.file_6],
            [sentinel.file_7, sentinel.file_8],
        ]

        files = svc.list_files("COURSE_ID")

        # It called the Blackboard API three times getting the three pages.
        assert basic_blackboard_api_client.request.call_args_list == [
            call("GET", "courses/uuid:COURSE_ID/resources?type=file&limit=200"),
            call("GET", "PAGE_2_PATH"),
            call("GET", "PAGE_3_PATH"),
        ]
        # It returned all three pages of files as a single list.
        assert files == [
            sentinel.file_1,
            sentinel.file_2,
            sentinel.file_3,
            sentinel.file_4,
            sentinel.file_5,
            sentinel.file_6,
            sentinel.file_7,
            sentinel.file_8,
        ]

    def test_it_doesnt_send_paginated_requests_forever(
        self, svc, basic_blackboard_api_client, blackboard_list_files_schema
    ):
        # Make the Blackboard API send next page paths forever.
        basic_blackboard_api_client.request.return_value = factories.requests.Response(
            json_data={"paging": {"nextPage": "NEXT_PAGE"}}
        )

        files = svc.list_files("COURSE_ID")

        assert basic_blackboard_api_client.request.call_count == PAGINATION_MAX_REQUESTS
        assert len(files) == PAGINATION_MAX_REQUESTS * len(
            blackboard_list_files_schema.parse.return_value
        )


class TestPublicURL:
    def test_it(
        self,
        svc,
        basic_blackboard_api_client,
        BlackboardPublicURLSchema,
        blackboard_public_url_schema,
    ):
        public_url = svc.public_url("COURSE_ID", "FILE_ID")

        basic_blackboard_api_client.request.assert_called_once_with(
            "GET", "courses/uuid:COURSE_ID/resources/FILE_ID"
        )
        BlackboardPublicURLSchema.assert_called_once_with(
            basic_blackboard_api_client.request.return_value
        )
        assert public_url == blackboard_public_url_schema.parse.return_value

    def test_it_raises_BlackboardFileNotFoundInCourse_if_the_Blackboard_API_404s(
        self, svc, basic_blackboard_api_client
    ):
        basic_blackboard_api_client.request.side_effect = HTTPError(
            factories.requests.Response(status_code=404)
        )

        with pytest.raises(BlackboardFileNotFoundInCourse):
            svc.public_url("COURSE_ID", "FILE_ID")

    def test_it_raises_HTTPError_if_the_Blackboard_API_fails_in_any_other_way(
        self, svc, basic_blackboard_api_client
    ):
        basic_blackboard_api_client.request.side_effect = HTTPError(
            factories.requests.Response(status_code=400)
        )

        with pytest.raises(HTTPError):
            svc.public_url("COURSE_ID", "FILE_ID")


@pytest.fixture
def svc(basic_blackboard_api_client):
    return BlackboardAPIClient(basic_blackboard_api_client)


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
