import json
from unittest import mock

import pytest
import requests

from lms.validation import (
    CanvasAuthenticatedUsersSectionsResponseSchema,
    CanvasCourseSectionsResponseSchema,
    CanvasListFilesResponseSchema,
    CanvasPublicURLResponseSchema,
    CanvasUsersSectionsResponseSchema,
    ValidationError,
)


def response():
    """Return a mock ``requests`` HTTP response object."""
    return mock.create_autospec(requests.Response, instance=True, spec_set=True)


def canvas_authenticated_users_sections_response_schema():
    """Return a CanvasAuthenticatedUsersSectionsResponseSchema."""
    response_ = response()
    response_.json.return_value = {
        "sections": [
            {"id": 101, "name": "section_name_1", "unexpected": "ignored"},
            {"id": 102, "name": "section_name_2"},
            {"id": 103, "name": "section_name_3"},
        ]
    }
    return CanvasAuthenticatedUsersSectionsResponseSchema(response_)


def canvas_course_sections_response_schema():
    """Return a CanvasCourseSectionsResponseSchema."""
    response_ = response()
    response_.json.return_value = [
        {"id": 101, "name": "section_name_1", "unexpected": "ignored"},
        {"id": 102, "name": "section_name_2"},
        {"id": 103, "name": "section_name_3"},
    ]
    return CanvasCourseSectionsResponseSchema(response_)


def canvas_users_sections_response_schema():
    """Return a CanvasUsersSectionsResponseSchema."""
    response_ = response()
    response_.json.return_value = {
        "enrollments": [
            {"course_section_id": 101, "foo": "bar"},
            {"course_section_id": 102, "foo": "bar"},
            {"course_section_id": 103, "foo": "bar"},
        ]
    }
    return CanvasUsersSectionsResponseSchema(response_)


def canvas_list_files_response_schema():
    """Return a CanvasListFilesResponseSchema."""
    response_ = response()
    response_.json.return_value = [
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
    return CanvasListFilesResponseSchema(response_)


def canvas_public_url_response_schema():
    """Return a CanvasPublicURLResponseSchema."""
    response_ = response()
    response_.json.return_value = {
        "public_url": "https://example-bucket.s3.amazonaws.com/example-namespace/attachments/1/example-filename?AWSAccessKeyId=example-key&Expires=1400000000&Signature=example-signature"
    }
    return CanvasPublicURLResponseSchema(response_)


class TestCommon:
    def test_it_raises_ValidationError_if_the_response_json_has_the_wrong_format(
        self, schema
    ):
        # The decoded JSON value is a string rather than a list or object.
        schema.context["response"].json.return_value = "wrong_format"

        with pytest.raises(ValidationError) as exc_info:
            schema.parse()

        assert exc_info.value.messages == {"_schema": ["Invalid input type."]}

    def test_it_raises_ValidationError_if_the_response_body_isnt_valid_json(
        self, schema
    ):
        # Calling response.json() will raise JSONDecodeError.
        schema.context["response"].json.side_effect = lambda: json.loads("invalid")

        with pytest.raises(ValidationError) as exc_info:
            schema.parse()

        assert exc_info.value.messages == {
            "_schema": ["response doesn't have a valid JSON body"]
        }

    @pytest.fixture(
        params=[
            canvas_authenticated_users_sections_response_schema,
            canvas_course_sections_response_schema,
            canvas_users_sections_response_schema,
            canvas_list_files_response_schema,
            canvas_public_url_response_schema,
        ]
    )
    def schema(self, request):
        return request.param()


class TestCanvasAuthenticatedUsersSectionsResponseSchema:
    def test_it_returns_a_list_of_valid_section_dicts(self, schema):
        parsed_params = schema.parse()

        assert parsed_params == [
            {"id": 101, "name": "section_name_1"},
            {"id": 102, "name": "section_name_2"},
            {"id": 103, "name": "section_name_3"},
        ]

    @pytest.mark.parametrize(
        "invalid_body,error_messages",
        [
            pytest.param(
                {},
                ["Missing data for required field."],
                id="There must be a sections key",
            ),
            pytest.param(
                {"sections": []},
                ["Shorter than minimum length 1."],
                id="There must be at least one section",
            ),
            pytest.param(
                {"sections": "not a list"},
                ["Not a valid list."],
                id="Sections must be a list",
            ),
            pytest.param(
                {"sections": ["not a dict", 1, False]},
                {
                    0: {"_schema": ["Invalid input type."]},
                    1: {"_schema": ["Invalid input type."]},
                    2: {"_schema": ["Invalid input type."]},
                },
                id="Each section must be a dict",
            ),
            pytest.param(
                {"sections": [{"name": "Test Section"}]},
                {0: {"id": ["Missing data for required field."]}},
                id="Each section dict must have an ID",
            ),
            pytest.param(
                {"sections": [{"id": "not an int", "name": "Test Section"}]},
                {0: {"id": ["Not a valid integer."]}},
                id="IDs must be ints",
            ),
            pytest.param(
                {"sections": [{"id": 101}]},
                {0: {"name": ["Missing data for required field."]}},
                id="Each section dict must have a name",
            ),
            pytest.param(
                {"sections": [{"id": 101, "name": 26}]},
                {0: {"name": ["Not a valid string."]}},
                id="Names must be strings",
            ),
        ],
    )
    def test_invalid(self, schema, invalid_body, error_messages):
        schema.context["response"].json.return_value = invalid_body

        with pytest.raises(ValidationError) as exc_info:
            schema.parse()

        assert exc_info.value.messages == {
            "sections": error_messages,
        }

    @pytest.fixture
    def schema(self):
        return canvas_authenticated_users_sections_response_schema()


class TestCanvasCourseSectionsResponseSchema:
    def test_it_returns_a_list_of_valid_section_dicts(self, schema):
        parsed_params = schema.parse()

        assert parsed_params == [
            {"id": 101, "name": "section_name_1"},
            {"id": 102, "name": "section_name_2"},
            {"id": 103, "name": "section_name_3"},
        ]

    @pytest.mark.parametrize(
        "invalid_body,error_messages",
        [
            pytest.param(
                [],
                {"_schema": ["Shorter than minimum length 1."]},
                id="There must be at least one section",
            ),
            pytest.param(
                {"this is": "not a list"},
                {"_schema": ["Invalid input type."]},
                id="Sections must be a list",
            ),
            pytest.param(
                ["not a dict", 1, False],
                {
                    0: {"_schema": ["Invalid input type."]},
                    1: {"_schema": ["Invalid input type."]},
                    2: {"_schema": ["Invalid input type."]},
                },
                id="Each section must be a dict",
            ),
            pytest.param(
                [{"name": "Test Section"}],
                {0: {"id": ["Missing data for required field."]}},
                id="Each section dict must have an ID",
            ),
            pytest.param(
                [{"id": "not an int", "name": "Test Section"}],
                {0: {"id": ["Not a valid integer."]}},
                id="IDs must be ints",
            ),
            pytest.param(
                [{"id": 101}],
                {0: {"name": ["Missing data for required field."]}},
                id="Each section dict must have a name",
            ),
            pytest.param(
                [{"id": 101, "name": 26}],
                {0: {"name": ["Not a valid string."]}},
                id="Names must be strings",
            ),
        ],
    )
    def test_invalid(self, schema, invalid_body, error_messages):
        schema.context["response"].json.return_value = invalid_body

        with pytest.raises(ValidationError) as exc_info:
            schema.parse()

        assert exc_info.value.messages == error_messages

    @pytest.fixture
    def schema(self):
        return canvas_course_sections_response_schema()


class TestCanvasUsersSectionsResponseSchema:
    def test_it_returns_a_list_of_valid_section_dicts(self, schema):
        parsed_params = schema.parse()

        assert parsed_params == [
            {"id": 101},
            {"id": 102},
            {"id": 103},
        ]

    @pytest.mark.parametrize(
        "invalid_body,error_messages",
        [
            pytest.param(
                {},
                ["Missing data for required field."],
                id="There must be an enrollments key",
            ),
            pytest.param(
                {"enrollments": []},
                ["Shorter than minimum length 1."],
                id="There must be at least one enrollment",
            ),
            pytest.param(
                {"enrollments": "not a list"},
                ["Not a valid list."],
                id="enrollments must be a list",
            ),
            pytest.param(
                {"enrollments": ["not a dict", 1, False]},
                {
                    0: {"_schema": ["Invalid input type."]},
                    1: {"_schema": ["Invalid input type."]},
                    2: {"_schema": ["Invalid input type."]},
                },
                id="Each enrollment must be a dict",
            ),
            pytest.param(
                {"enrollments": [{"foo": "bar"}]},
                {0: {"course_section_id": ["Missing data for required field."]}},
                id="Each enrollment dict must have a course_section_id",
            ),
            pytest.param(
                {"enrollments": [{"course_section_id": "not an int"}]},
                {0: {"course_section_id": ["Not a valid integer."]}},
                id="course_section_id's must be ints",
            ),
        ],
    )
    def test_invalid(self, schema, invalid_body, error_messages):
        schema.context["response"].json.return_value = invalid_body

        with pytest.raises(ValidationError) as exc_info:
            schema.parse()

        assert exc_info.value.messages == {
            "enrollments": error_messages,
        }

    @pytest.fixture
    def schema(self):
        return canvas_users_sections_response_schema()


class TestCanvasListFilesResponseSchema:
    def test_it_returns_the_list_of_files(self, schema):
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

    def test_it_returns_an_empty_list_if_there_are_no_files(self, schema):
        schema.context["response"].json.return_value = []

        parsed_params = schema.parse()

        assert parsed_params == []

    @pytest.mark.parametrize("field_name", ["display_name", "id", "updated_at"])
    def test_it_raises_ValidationError_if_a_file_is_missing_a_required_field(
        self, field_name, schema
    ):
        del schema.context["response"].json.return_value[1][field_name]

        with pytest.raises(ValidationError) as exc_info:
            schema.parse()

        assert exc_info.value.messages == {
            1: {field_name: ["Missing data for required field."]}
        }

    def test_it_raises_ValidationError_if_one_of_the_objects_in_the_response_json_has_the_wrong_format(
        self, schema
    ):
        # One item in the list is not an object.
        schema.context["response"].json.return_value = (
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

        assert exc_info.value.messages == {0: {"_schema": ["Invalid input type."]}}

    @pytest.fixture
    def schema(self):
        return canvas_list_files_response_schema()


class TestCanvasPublicURLResponseSchema:
    def test_it_returns_the_public_url(self, schema):
        parsed_params = schema.parse()

        assert parsed_params == {
            "public_url": "https://example-bucket.s3.amazonaws.com/example-namespace/attachments/1/example-filename?AWSAccessKeyId=example-key&Expires=1400000000&Signature=example-signature"
        }

    def test_it_raises_ValidationError_if_the_public_url_is_missing(self, schema):
        del schema.context["response"].json.return_value["public_url"]

        with pytest.raises(ValidationError) as exc_info:
            schema.parse()

        assert exc_info.value.messages == {
            "public_url": ["Missing data for required field."]
        }

    @pytest.mark.parametrize("invalid_url", [23, True, ["a", "b", "c"], {}])
    def test_it_raises_ValidationError_if_the_public_url_has_the_wrong_type(
        self, schema, invalid_url
    ):
        schema.context["response"].json.return_value["public_url"] = invalid_url

        with pytest.raises(ValidationError) as exc_info:
            schema.parse()

        assert exc_info.value.messages == {"public_url": ["Not a valid string."]}

    @pytest.fixture
    def schema(self):
        return canvas_public_url_response_schema()
