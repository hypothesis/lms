import json

import pytest

from lms.validation import ValidationError
from lms.validation._api import APIRecordSpeedgraderSchema, APIRecordResultSchema


class TestAPIRecordSpeedgraderSchema:
    def test_it_parses_request(self, pyramid_request, all_fields):
        pyramid_request.body = json.dumps(all_fields)

        schema = APIRecordSpeedgraderSchema(pyramid_request)
        parsed_params = schema.parse()

        assert parsed_params == all_fields

    @pytest.mark.parametrize(
        "field", ["h_username", "lis_outcome_service_url", "lis_result_sourcedid"]
    )
    def test_it_raises_if_required_fields_missing(
        self, pyramid_request, all_fields, field
    ):
        del all_fields[field]
        pyramid_request.body = json.dumps(all_fields)

        schema = APIRecordSpeedgraderSchema(pyramid_request)

        with pytest.raises(ValidationError):
            schema.parse()

    @pytest.mark.parametrize("field", ["document_url", "canvas_file_id"])
    def test_it_doesnt_raise_if_optional_fields_missing(
        self, pyramid_request, all_fields, field
    ):
        del all_fields[field]
        pyramid_request.body = json.dumps(all_fields)

        schema = APIRecordSpeedgraderSchema(pyramid_request)
        schema.parse()

    @pytest.fixture
    def all_fields(self):
        return {
            "document_url": "https://example.com",
            "canvas_file_id": "file123",
            "h_username": "user123",
            "lis_outcome_service_url": "https://hypothesis.shinylms.com/outcomes",
            "lis_result_sourcedid": "modelstudent-assignment1",
        }


class TestAPIRecordResultSchema:
    def test_it_parses_request(self, pyramid_request, all_fields):
        pyramid_request.body = json.dumps(all_fields)

        schema = APIRecordResultSchema(pyramid_request)
        parsed_params = schema.parse()

        assert parsed_params == all_fields

    @pytest.mark.parametrize(
        "field", ["lis_outcome_service_url", "lis_result_sourcedid", "score"]
    )
    def test_it_raises_if_required_fields_missing(
        self, pyramid_request, all_fields, field
    ):
        del all_fields[field]
        pyramid_request.body = json.dumps(all_fields)

        schema = APIRecordResultSchema(pyramid_request)

        with pytest.raises(ValidationError):
            schema.parse()

    @pytest.mark.parametrize("bad_score", ["5", 5.0, 5, -1, 1.2, "fingers"])
    def test_it_raises_if_score_invalid(self, pyramid_request, all_fields, bad_score):
        all_fields["score"] = bad_score
        pyramid_request.body = json.dumps(all_fields)

        schema = APIRecordResultSchema(pyramid_request)

        with pytest.raises(ValidationError):
            schema.parse()

    @pytest.mark.parametrize("good_score", ["0", "0.5", "1", "1.0", "0.0", 0.5, 1, 0])
    def test_it_does_not_raise_with_valid_score_value(
        self, pyramid_request, all_fields, good_score
    ):
        all_fields["score"] = good_score
        pyramid_request.body = json.dumps(all_fields)

        schema = APIRecordResultSchema(pyramid_request)

        schema.parse()

    @pytest.fixture
    def all_fields(self):
        return {
            "lis_outcome_service_url": "https://hypothesis.shinylms.com/outcomes",
            "lis_result_sourcedid": "modelstudent-assignment1",
            "score": 0.5,
        }
