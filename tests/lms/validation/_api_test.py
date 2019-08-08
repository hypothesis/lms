import json

import pytest

from lms.validation import ValidationError
from lms.validation._api import APIRecordSubmissionSchema


class TestAPIRecordSubmissionSchema:
    def test_it_parses_request(self, pyramid_request, all_fields):
        pyramid_request.body = json.dumps(all_fields)

        schema = APIRecordSubmissionSchema(pyramid_request)
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

        schema = APIRecordSubmissionSchema(pyramid_request)

        with pytest.raises(ValidationError):
            schema.parse()

    @pytest.mark.parametrize("field", ["document_url", "canvas_file_id"])
    def test_it_doesnt_raise_if_optional_fields_missing(
        self, pyramid_request, all_fields, field
    ):
        del all_fields[field]
        pyramid_request.body = json.dumps(all_fields)

        schema = APIRecordSubmissionSchema(pyramid_request)
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
