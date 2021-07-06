import pytest

from lms.validation._exceptions import ValidationError
from lms.views.api.blackboard._schemas import (
    BlackboardListFilesSchema,
    BlackboardPublicURLSchema,
)
from tests import factories


class TestBlackboardListFilesSchema:
    def test_valid(self, list_files_response):
        schema = BlackboardListFilesSchema(
            factories.requests.Response(json_data=list_files_response)
        )

        result = schema.parse()

        assert result == [
            {
                "id": "blackboard://content-resource/_7851_0/",
                "updated_at": "2008-05-06T07:26:35.000z",
                "display_name": "File_0.pdf",
                "type": "File",
            },
            {
                "id": "blackboard://content-resource/_7851_1/",
                "updated_at": "1983-05-26T02:37:23.000z",
                "display_name": "File_1.pdf",
                "type": "File",
            },
            {
                "id": "blackboard://content-resource/_7851_2/",
                "updated_at": "1983-05-26T02:37:23.000z",
                "display_name": "Folder_1",
                "type": "Folder",
            },
        ]

    def test_it_raises_if_results_is_missing(self, list_files_response):
        del list_files_response["results"]

        assert_raises(BlackboardListFilesSchema, list_files_response)

    def test_it_raises_if_results_isnt_a_list(self, list_files_response):
        list_files_response["results"] = None

        assert_raises(BlackboardListFilesSchema, list_files_response)

    @pytest.mark.parametrize("missing_field", ["id", "modified", "name"])
    def test_it_raises_if_a_required_field_is_missing(
        self, list_files_response, missing_field
    ):
        del list_files_response["results"][0][missing_field]

        assert_raises(BlackboardListFilesSchema, list_files_response)

    @pytest.mark.parametrize("invalid_field", ["id", "modified", "name"])
    def test_it_raises_if_a_field_is_invalid(self, list_files_response, invalid_field):
        list_files_response["results"][0][invalid_field] = 23

        assert_raises(BlackboardListFilesSchema, list_files_response)


class TestBlackboardPublicURLSchema:
    def test_valid(self, single_file_response):
        schema = BlackboardPublicURLSchema(
            factories.requests.Response(json_data=single_file_response)
        )

        result = schema.parse()

        assert result == "https://example.com/file0.pdf"

    def test_it_raises_if_a_the_body_isnt_a_dict(self):
        assert_raises(BlackboardPublicURLSchema, [])

    @pytest.mark.parametrize("missing_field", ["id", "modified", "name"])
    def test_it_raises_if_a_required_field_is_missing(
        self, single_file_response, missing_field
    ):
        del single_file_response[missing_field]

        assert_raises(BlackboardPublicURLSchema, single_file_response)

    @pytest.mark.parametrize("invalid_field", ["id", "modified", "name"])
    def test_it_raises_if_a_field_is_invalid(self, single_file_response, invalid_field):
        single_file_response[invalid_field] = 23

        assert_raises(BlackboardPublicURLSchema, single_file_response)

    @pytest.fixture
    def single_file_response(self, list_files_response):
        # The response body from the single-file API looks the same as a single
        # one of the file dicts from the list-files API.
        return list_files_response["results"][0]


@pytest.fixture
def list_files_response():
    """Return the JSON body of a valid Blackboard Files API response."""
    return {
        "results": [
            {
                "id": "_7851_0",
                "modified": "2008-05-06T07:26:35.000z",
                "name": "File_0.pdf",
                "downloadUrl": "https://example.com/file0.pdf",
                "type": "File",
                "mimeType": "application/pdf",
                "unknown_field": "this_should_be_excluded",
            },
            {
                "id": "_7851_1",
                "modified": "1983-05-26T02:37:23.000z",
                "name": "File_1.pdf",
                "downloadUrl": "https://example.com/file1.pdf",
                "type": "File",
                "mimeType": "application/pdf",
            },
            # A folder (notice: these have no downloadUrl or mimeType).
            {
                "id": "_7851_2",
                "modified": "1983-05-26T02:37:23.000z",
                "name": "Folder_1",
                "type": "Folder",
            },
            # A non-PDF file. This should get filtered out.
            {
                "id": "_7851_3",
                "modified": "1980-05-26T02:37:23.000z",
                "name": "NOT_A_PDF.jpeg",
                "downloadUrl": "https://example.com/NOT_A_PDF.jpeg",
                "type": "File",
                "mimeType": "image/jpeg",
            },
        ]
    }


def assert_raises(schema_class, json_data):
    """Assert that the schema raises when parsing json_data."""
    schema = schema_class(factories.requests.Response(json_data=json_data))

    with pytest.raises(ValidationError):
        schema.parse()
