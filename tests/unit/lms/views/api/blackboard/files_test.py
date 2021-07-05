from unittest.mock import call, sentinel

import pytest

from lms.services import HTTPError
from lms.views.api.blackboard.exceptions import BlackboardFileNotFoundInCourse
from lms.views.api.blackboard.files import (
    PAGINATION_MAX_REQUESTS,
    BlackboardFilesAPIViews,
)
from tests import factories

pytestmark = pytest.mark.usefixtures("oauth2_token_service", "blackboard_api_client")


class TestListFiles:
    def test_it(
        self,
        view,
        blackboard_api_client,
        BlackboardListFilesSchema,
        blackboard_list_files_schema,
    ):
        blackboard_api_client.request.return_value = factories.requests.Response(
            json_data={}
        )
        blackboard_list_files_schema.parse.return_value = [
            sentinel.file_1,
            sentinel.file_2,
            sentinel.file_3,
        ]

        files = view()

        blackboard_api_client.request.assert_called_once_with(
            "GET", "courses/uuid:COURSE_ID/resources?limit=200"
        )
        BlackboardListFilesSchema.assert_called_once_with(
            blackboard_api_client.request.return_value
        )
        assert files == blackboard_list_files_schema.parse.return_value

    def test_it_with_pagination(
        self, view, blackboard_api_client, blackboard_list_files_schema
    ):
        # Each response from the Blackboard API includes the path to the next
        # page in the JSON body. This is the whole path to the next page,
        # including limit and offset query params, as a string. For example:
        # "/learn/api/public/v1/courses/uuid:<ID>/resources?limit=200&offset=200"
        #
        blackboard_api_client.request.side_effect = [
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

        files = view()

        # It called the Blackboard API three times getting the three pages.
        assert blackboard_api_client.request.call_args_list == [
            call("GET", "courses/uuid:COURSE_ID/resources?limit=200"),
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
        self, view, blackboard_api_client, blackboard_list_files_schema
    ):
        # Make the Blackboard API send next page paths forever.
        blackboard_api_client.request.return_value = factories.requests.Response(
            json_data={"paging": {"nextPage": "NEXT_PAGE"}}
        )

        files = view()

        assert blackboard_api_client.request.call_count == PAGINATION_MAX_REQUESTS
        assert len(files) == PAGINATION_MAX_REQUESTS * len(
            blackboard_list_files_schema.parse.return_value
        )

    @pytest.fixture(autouse=True)
    def pyramid_request(self, pyramid_request):
        pyramid_request.matchdict["course_id"] = "COURSE_ID"
        return pyramid_request

    @pytest.fixture
    def view(self, views):
        return views.list_files


class TestViaURL:
    def test_it(
        self,
        view,
        pyramid_request,
        blackboard_api_client,
        BlackboardPublicURLSchema,
        blackboard_public_url_schema,
        helpers,
    ):
        response = view()

        blackboard_api_client.request.assert_called_once_with(
            "GET", "courses/uuid:COURSE_ID/resources/FILE_ID"
        )
        BlackboardPublicURLSchema.assert_called_once_with(
            blackboard_api_client.request.return_value
        )
        helpers.via_url.assert_called_once_with(
            pyramid_request,
            blackboard_public_url_schema.parse.return_value,
            content_type="pdf",
        )
        assert response == {"via_url": helpers.via_url.return_value}

    def test_it_raises_BlackboardFileNotFoundInCourse_if_the_Blackboard_API_404s(
        self, view, blackboard_api_client
    ):
        blackboard_api_client.request.side_effect = HTTPError(
            factories.requests.Response(status_code=404)
        )

        with pytest.raises(BlackboardFileNotFoundInCourse):
            view()

    def test_it_raises_HTTPError_if_the_Blackboard_API_fails_in_any_other_way(
        self, view, blackboard_api_client
    ):
        blackboard_api_client.request.side_effect = HTTPError(
            factories.requests.Response(status_code=400)
        )

        with pytest.raises(HTTPError):
            view()

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.matchdict["course_id"] = "COURSE_ID"
        pyramid_request.params[
            "document_url"
        ] = "blackboard://content-resource/FILE_ID/"
        return pyramid_request

    @pytest.fixture
    def view(self, views):
        return views.via_url


@pytest.fixture(autouse=True)
def helpers(patch):
    return patch("lms.views.api.blackboard.files.helpers")


@pytest.fixture
def views(pyramid_request):
    return BlackboardFilesAPIViews(pyramid_request)


@pytest.fixture(autouse=True)
def BlackboardListFilesSchema(patch):
    return patch("lms.views.api.blackboard.files.BlackboardListFilesSchema")


@pytest.fixture
def blackboard_list_files_schema(BlackboardListFilesSchema):
    return BlackboardListFilesSchema.return_value


@pytest.fixture(autouse=True)
def BlackboardPublicURLSchema(patch):
    return patch("lms.views.api.blackboard.files.BlackboardPublicURLSchema")


@pytest.fixture
def blackboard_public_url_schema(BlackboardPublicURLSchema):
    return BlackboardPublicURLSchema.return_value
