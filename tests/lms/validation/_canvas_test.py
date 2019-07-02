import json
from unittest import mock

import pytest
import requests

from lms.validation import (
    CanvasListFilesResponseSchema,
    CanvasPublicURLResponseSchema,
    ValidationError,
)


class CommonResponseSchemaTests:
    def test_it_raises_ValidationError_if_the_response_json_has_the_wrong_format(
        self, response, schema
    ):
        # The decoded JSON value is a string rather than a list or object.
        response.json.return_value = "wrong_format"
        schema.context["response"] = response

        with pytest.raises(ValidationError) as exc_info:
            schema.parse()

        assert exc_info.value.messages == {"_schema": ["Invalid input type."]}

    def test_it_raises_ValidationError_if_the_response_body_isnt_valid_json(
        self, response, schema
    ):
        # Calling response.json() will raise JSONDecodeError.
        response.json.side_effect = lambda: json.loads("invalid")
        schema.context["response"] = response

        with pytest.raises(ValidationError) as exc_info:
            schema.parse()

        assert exc_info.value.messages == {
            "_schema": ["response doesn't have a valid JSON body"]
        }


class TestCanvasListFilesResponseSchema(CommonResponseSchemaTests):
    def test_it_returns_the_list_of_files(self, schema, list_files_response):
        parsed_params = schema.parse()

        assert parsed_params == [
            {
                "display_name": "TEST FILE 1",
                "id": 188,
                "updated_at": "2019-05-08T15:22:31Z",
            },
            {
                "display_name": "TEST FILE 2",
                "id": 181,
                "updated_at": "2019-02-14T00:33:01Z",
            },
            {
                "display_name": "TEST FILE 3",
                "id": 97,
                "updated_at": "2018-10-19T17:16:50Z",
            },
        ]

    def test_it_returns_an_empty_list_if_there_are_no_files(
        self, schema, list_files_response
    ):
        list_files_response.json.return_value = []

        parsed_params = schema.parse()

        assert parsed_params == []

    @pytest.mark.parametrize("field_name", ["display_name", "id", "updated_at"])
    def test_it_raises_ValidationError_if_a_file_is_missing_a_required_field(
        self, field_name, schema, list_files_response
    ):
        del list_files_response.json.return_value[1][field_name]

        with pytest.raises(ValidationError) as exc_info:
            schema.parse()

        assert exc_info.value.messages == {
            1: {field_name: ["Missing data for required field."]}
        }

    def test_it_raises_ValidationError_if_one_of_the_objects_in_the_response_json_has_the_wrong_format(
        self, schema, list_files_response
    ):
        # One item in the list is not an object.
        list_files_response.json.return_value = (
            [
                {
                    "display_name": "TEST FILE 1",
                    "id": 188,
                    "updated_at": "2019-05-08T15:22:31Z",
                },
                True,
                {
                    "display_name": "TEST FILE 3",
                    "id": 97,
                    "updated_at": "2018-10-19T17:16:50Z",
                },
            ],
        )

        with pytest.raises(ValidationError) as exc_info:
            schema.parse()

        assert exc_info.value.messages == {0: {}, "_schema": ["Invalid input type."]}

    @pytest.fixture
    def schema(self, list_files_response):
        return CanvasListFilesResponseSchema(list_files_response)

    @pytest.fixture
    def list_files_response(self, response):
        """
        Return a Canvas list files API response.

        Same fields and format as real Canvas list files API responses.
        """
        response.json.return_value = [
            {
                "content-type": "application/pdf",
                "created_at": "2018-11-22T08:46:38Z",
                "display_name": "TEST FILE 1",
                "filename": "TEST_FILE_1.pdf",
                "folder_id": 81,
                "hidden": False,
                "hidden_for_user": False,
                "id": 188,
                "lock_at": None,
                "locked": False,
                "locked_for_user": False,
                "media_entry_id": None,
                "mime_class": "pdf",
                "modified_at": "2018-11-22T08:46:38Z",
                "size": 2435546,
                "thumbnail_url": None,
                "unlock_at": None,
                "updated_at": "2019-05-08T15:22:31Z",
                "upload_status": "success",
                "url": "TEST_URL_1",
                "uuid": "TEST_UUID_1",
                "workflow_state": "processing",
            },
            {
                "content-type": "application/pdf",
                "created_at": "2018-10-25T15:04:08Z",
                "display_name": "TEST FILE 2",
                "filename": "TEST_FILE_2.pdf",
                "folder_id": 17,
                "hidden": False,
                "hidden_for_user": False,
                "id": 181,
                "lock_at": None,
                "locked": False,
                "locked_for_user": False,
                "media_entry_id": None,
                "mime_class": "pdf",
                "modified_at": "2018-10-25T15:04:08Z",
                "size": 1407214,
                "thumbnail_url": None,
                "unlock_at": None,
                "updated_at": "2019-02-14T00:33:01Z",
                "upload_status": "success",
                "url": "TEST_URL_2",
                "uuid": "TEST_UUID_2",
                "workflow_state": "processing",
            },
            {
                "content-type": "application/pdf",
                "created_at": "2017-09-08T11:05:03Z",
                "display_name": "TEST FILE 3",
                "filename": "TEST_FILE_3.pdf",
                "folder_id": 17,
                "hidden": False,
                "hidden_for_user": False,
                "id": 97,
                "lock_at": None,
                "locked": False,
                "locked_for_user": False,
                "media_entry_id": None,
                "mime_class": "pdf",
                "modified_at": "2017-09-08T11:05:03Z",
                "size": 265615,
                "thumbnail_url": None,
                "unlock_at": None,
                "updated_at": "2018-10-19T17:16:50Z",
                "upload_status": "success",
                "url": "TEST_URL_3",
                "uuid": "TEST_UUID_3",
                "workflow_state": "processing",
            },
        ]
        return response


class TestCanvasPublicURLResponseSchema(CommonResponseSchemaTests):
    def test_it_returns_the_public_url(self, schema, public_url_response):
        parsed_params = schema.parse()

        assert parsed_params == {
            "public_url": "https://example-bucket.s3.amazonaws.com/example-namespace/attachments/1/example-filename?AWSAccessKeyId=example-key&Expires=1400000000&Signature=example-signature"
        }

    def test_it_raises_ValidationError_if_the_public_url_is_missing(
        self, schema, public_url_response
    ):
        del public_url_response.json.return_value["public_url"]

        with pytest.raises(ValidationError) as exc_info:
            schema.parse()

        assert exc_info.value.messages == {
            "public_url": ["Missing data for required field."]
        }

    @pytest.mark.parametrize("invalid_url", [23, True, ["a", "b", "c"], {}])
    def test_it_raises_ValidationError_if_the_public_url_has_the_wrong_type(
        self, schema, public_url_response, invalid_url
    ):
        public_url_response.json.return_value["public_url"] = invalid_url

        with pytest.raises(ValidationError) as exc_info:
            schema.parse()

        assert exc_info.value.messages == {"public_url": ["Not a valid string."]}

    @pytest.fixture
    def schema(self, public_url_response):
        return CanvasPublicURLResponseSchema(public_url_response)

    @pytest.fixture
    def public_url_response(self, response):
        response.json.return_value = {
            "public_url": "https://example-bucket.s3.amazonaws.com/example-namespace/attachments/1/example-filename?AWSAccessKeyId=example-key&Expires=1400000000&Signature=example-signature"
        }
        return response


@pytest.fixture
def response():
    """Return a ``requests`` HTTP response object."""
    return mock.create_autospec(requests.Response, instance=True, spec_set=True)
