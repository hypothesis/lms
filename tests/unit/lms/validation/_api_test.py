import json

import pytest

from lms.validation import ValidationError
from lms.validation._api import (
    APIBlackboardSyncSchema,
    APICreateAssignmentSchema,
    APIReadResultSchema,
    APIRecordResultSchema,
    APIRecordSpeedgraderSchema,
)


class TestAPIRecordSpeedgraderSchema:
    def test_it_parses_request(self, json_request, all_fields):
        request = json_request(all_fields)

        parsed_params = APIRecordSpeedgraderSchema(request).parse()

        assert parsed_params == all_fields

    @pytest.mark.parametrize(
        "field",
        [
            "h_username",
            "lis_outcome_service_url",
            "lis_result_sourcedid",
            "learner_canvas_user_id",
        ],
    )
    def test_it_raises_if_required_fields_missing(
        self, json_request, all_fields, field
    ):
        request = json_request(all_fields, exclude=[field])

        schema = APIRecordSpeedgraderSchema(request)

        with pytest.raises(ValidationError):
            schema.parse()

    @pytest.mark.parametrize("field", ["document_url", "canvas_file_id"])
    def test_it_doesnt_raise_if_optional_fields_missing(
        self, json_request, all_fields, field
    ):
        request = json_request(all_fields, exclude=[field])

        APIRecordSpeedgraderSchema(request).parse()

    def test_it_doesnt_raise_null_group_set(self, json_request, all_fields):
        all_fields["group_set"] = None  # Present, but set to None

        request = json_request(all_fields)

        APIRecordSpeedgraderSchema(request).parse()

    @pytest.fixture
    def all_fields(self):
        return {
            "document_url": "https://example.com",
            "canvas_file_id": "file123",
            "h_username": "user123",
            "learner_canvas_user_id": "canvas_user_123",
            "lis_outcome_service_url": "https://hypothesis.shinylms.com/outcomes",
            "lis_result_sourcedid": "modelstudent-assignment1",
            "group_set": 1,
        }


class TestAPIReadResultSchema:
    def test_it_parses_fields_from_query_params(self, pyramid_request, all_fields):
        for key in all_fields:
            pyramid_request.GET[key] = all_fields[key]

        schema = APIReadResultSchema(pyramid_request)
        parsed_params = schema.parse()

        assert parsed_params == all_fields

    def test_it_ignores_fields_in_json_body(self, pyramid_request, all_fields):
        pyramid_request.body = json.dumps(all_fields)

        schema = APIReadResultSchema(pyramid_request)
        with pytest.raises(ValidationError):
            schema.parse()

    @pytest.mark.parametrize(
        "field", ["lis_outcome_service_url", "lis_result_sourcedid"]
    )
    def test_it_raises_if_required_fields_missing(
        self, pyramid_request, all_fields, field
    ):
        del all_fields[field]
        pyramid_request.body = json.dumps(all_fields)

        schema = APIReadResultSchema(pyramid_request)

        with pytest.raises(ValidationError):
            schema.parse()

    @pytest.fixture
    def all_fields(self):
        return {
            "lis_outcome_service_url": "https://hypothesis.shinylms.com/outcomes",
            "lis_result_sourcedid": "modelstudent-assignment1",
        }


class TestAPIRecordResultSchema:
    def test_it_parses_request(self, json_request, all_fields):
        request = json_request(all_fields)

        parsed_params = APIRecordResultSchema(request).parse()

        assert parsed_params == all_fields

    @pytest.mark.parametrize(
        "field", ["lis_outcome_service_url", "lis_result_sourcedid", "score"]
    )
    def test_it_raises_if_required_fields_missing(
        self, json_request, all_fields, field
    ):
        request = json_request(all_fields, exclude=[field])

        schema = APIRecordResultSchema(request)

        with pytest.raises(ValidationError):
            schema.parse()

    @pytest.mark.parametrize("bad_score", ["5", 5.0, 5, -1, 1.2, "fingers"])
    def test_it_raises_if_score_invalid(self, json_request, all_fields, bad_score):
        request = json_request(dict(all_fields, score=bad_score))

        schema = APIRecordResultSchema(request)

        with pytest.raises(ValidationError):
            schema.parse()

    @pytest.mark.parametrize("good_score", ["0", "0.5", "1", "1.0", "0.0", 0.5, 1, 0])
    def test_it_does_not_raise_with_valid_score_value(
        self, json_request, all_fields, good_score
    ):
        request = json_request(dict(all_fields, score=good_score))

        APIRecordResultSchema(request).parse()

    @pytest.fixture
    def all_fields(self):
        return {
            "lis_outcome_service_url": "https://hypothesis.shinylms.com/outcomes",
            "lis_result_sourcedid": "modelstudent-assignment1",
            "score": 0.5,
        }


class TestAPICreateAssignmentSchema:
    @pytest.mark.parametrize(
        "assignment_fixture_name",
        ["url_assignment", "file_assignment", "vitalsource_assignment"],
    )
    def test_it_doesnt_raise_valid__assignment(
        self, json_request, assignment_fixture_name, request
    ):
        assignment_body = request.getfixturevalue(assignment_fixture_name)

        request = json_request(assignment_body)
        schema = APICreateAssignmentSchema(request)

        schema.parse()

    def test_it_raises_for_missing_book_id(self, json_request, vitalsource_assignment):
        del vitalsource_assignment["content"]["bookID"]
        request = json_request(vitalsource_assignment)
        schema = APICreateAssignmentSchema(request)

        with pytest.raises(ValidationError):
            schema.parse()

    def test_it_raises_for_missing_cfi(self, json_request, vitalsource_assignment):
        del vitalsource_assignment["content"]["cfi"]
        request = json_request(vitalsource_assignment)
        schema = APICreateAssignmentSchema(request)

        with pytest.raises(ValidationError):
            schema.parse()

    def test_it_raises_for_missing_url(self, json_request, url_assignment):
        del url_assignment["content"]["url"]
        request = json_request(url_assignment)
        schema = APICreateAssignmentSchema(request)

        with pytest.raises(ValidationError):
            schema.parse()

    def test_it_raises_for_missing_file(self, json_request, file_assignment):
        del file_assignment["content"]["file"]
        request = json_request(file_assignment)
        schema = APICreateAssignmentSchema(request)

        with pytest.raises(ValidationError):
            schema.parse()

    @pytest.fixture
    def vitalsource_assignment(self):
        return {
            "content": {
                "type": "vitalsource",
                "bookID": "BOOK_ID",
                "cfi": "CFI",
            },
            "course_id": "COURSE_ID",
            "ext_lti_assignment_id": "EXT_LTI_ASSIGNMENT_ID",
        }

    @pytest.fixture
    def url_assignment(self):
        return {
            "content": {
                "type": "url",
                "url": "https://example.com",
            },
            "course_id": "COURSE_ID",
            "ext_lti_assignment_id": "EXT_LTI_ASSIGNMENT_ID",
        }

    @pytest.fixture
    def file_assignment(self):
        return {
            "content": {
                "type": "file",
                "file": {
                    "display_name": "File 1",
                    "id": 1,
                    "updated_at": "today",
                    "size": 1000,
                },
            },
            "course_id": "COURSE_ID",
            "ext_lti_assignment_id": "EXT_LTI_ASSIGNMENT_ID",
        }


class TestAPIBlackboardSyncSchema:
    def test_it_parses_request(self, json_request, all_fields):
        request = json_request(all_fields)

        parsed_params = APIBlackboardSyncSchema(request).parse()

        assert parsed_params == all_fields

    @pytest.mark.parametrize(
        "field",
        [
            "lms",
            "course",
            "assignment",
            "group_info",
        ],
    )
    def test_it_raises_if_required_fields_missing(
        self, json_request, all_fields, field
    ):
        request = json_request(all_fields, exclude=[field])

        schema = APIBlackboardSyncSchema(request)

        with pytest.raises(ValidationError):
            schema.parse()

    @pytest.mark.parametrize("field", ["gradingStudentId"])
    def test_it_doesnt_raise_if_optional_fields_missing(
        self, json_request, all_fields, field
    ):
        request = json_request(all_fields, exclude=[field])

        APIBlackboardSyncSchema(request).parse()

    @pytest.fixture
    def all_fields(self):
        return {
            "lms": {"tool_consumer_instance_guid": "tool_consumer_instance_guid"},
            "course": {"context_id": "context_id"},
            "assignment": {"resource_link_id": "resource_link_id"},
            "group_info": {"some": "data"},
            "gradingStudentId": "gradingStudentId",
        }


@pytest.fixture
def json_request(pyramid_request):
    def _make_json_request(data, exclude=None):
        pyramid_request.content_type = pyramid_request.headers[
            "content-type"
        ] = "application/json"

        if exclude:
            for field in exclude:
                data.pop(field, None)

        pyramid_request.body = json.dumps(data)
        return pyramid_request

    return _make_json_request
