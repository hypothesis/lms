import datetime
from datetime import timezone
from unittest import mock
from urllib.parse import urlencode

import pytest

from lms.services.lti_outcomes import LTIOutcomesClient, LTIOutcomesRequestParams
from lms.views.api.lti import LTIOutcomesViews


class TestRecordCanvasSpeedgraderSubmission:
    def test_it_passes_correct_params_to_read_current_score(
        self, pyramid_request, lti_outcomes_client
    ):
        LTIOutcomesViews(pyramid_request).record_canvas_speedgrader_submission()

        lti_outcomes_client.read_result.assert_called_once_with(
            LTIOutcomesRequestParams(
                lis_outcome_service_url="https://hypothesis.shinylms.com/outcomes",
                lis_result_sourcedid="modelstudent-assignment1",
            )
        )

    def test_it_does_not_record_result_if_score_already_exists(
        self, pyramid_request, lti_outcomes_client
    ):
        lti_outcomes_client.read_result.return_value = 0.5

        LTIOutcomesViews(pyramid_request).record_canvas_speedgrader_submission()

        lti_outcomes_client.record_result.assert_not_called()

    @pytest.mark.parametrize(
        "document_url,canvas_file_id,lti_launch_doc_params",
        [
            ("https://example.com", None, {"url": "https://example.com"}),
            (None, "file123", {"canvas_file": "true", "file_id": "file123"}),
        ],
    )
    def test_it_records_result_if_no_score_exists(
        self,
        pyramid_request,
        lti_outcomes_client,
        document_url,
        canvas_file_id,
        lti_launch_doc_params,
    ):
        pyramid_request.parsed_params.update(
            {"document_url": document_url, "canvas_file_id": canvas_file_id}
        )
        lti_outcomes_client.read_result.return_value = None

        LTIOutcomesViews(pyramid_request).record_canvas_speedgrader_submission()

        expected_outcome_params = LTIOutcomesRequestParams(
            lis_outcome_service_url="https://hypothesis.shinylms.com/outcomes",
            lis_result_sourcedid="modelstudent-assignment1",
        )
        expected_submitted_at = datetime.datetime(2001, 1, 1, tzinfo=timezone.utc)
        expected_launch_url = "http://example.com/lti_launches?" + urlencode(
            {"focused_user": "user123", **lti_launch_doc_params}
        )
        lti_outcomes_client.record_result.assert_called_once_with(
            expected_outcome_params,
            lti_launch_url=expected_launch_url,
            submitted_at=expected_submitted_at,
        )

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.parsed_params = {
            # Information that is needed to construct the LTI launch URL for
            # Canvas's SpeedGrader.
            "h_username": "user123",
            # In practice, only one of `document_url` or `cnavas_file_id` will
            # be set.
            "document_url": "https://example.com",
            "canvas_file_id": "file456",
            # Metadata provided by LMS for requests to LTI Outcomes Management
            # service.
            "lis_outcome_service_url": "https://hypothesis.shinylms.com/outcomes",
            "lis_result_sourcedid": "modelstudent-assignment1",
        }
        return pyramid_request


class TestReadResult:
    def test_it_proxies_to_read_result(self, pyramid_request, lti_outcomes_client):
        LTIOutcomesViews(pyramid_request).read_result()

        expected_outcome_params = LTIOutcomesRequestParams(
            lis_outcome_service_url="https://hypothesis.shinylms.com/outcomes",
            lis_result_sourcedid="modelstudent-assignment1",
        )
        lti_outcomes_client.read_result.assert_called_once_with(expected_outcome_params)

    def test_it_returns_current_score(self, pyramid_request, lti_outcomes_client):
        lti_outcomes_client.read_result.return_value = 0.5

        current_score = LTIOutcomesViews(pyramid_request).read_result()

        assert current_score == {"currentScore": 0.5}

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.parsed_params = {
            # Metadata provided by LMS for requests to LTI Outcomes Management
            # service.
            "lis_outcome_service_url": "https://hypothesis.shinylms.com/outcomes",
            "lis_result_sourcedid": "modelstudent-assignment1",
        }
        return pyramid_request


class TestRecordResult:
    def test_it_records_result(self, pyramid_request, lti_outcomes_client):
        LTIOutcomesViews(pyramid_request).record_result()

        expected_outcome_params = LTIOutcomesRequestParams(
            lis_outcome_service_url="https://hypothesis.shinylms.com/outcomes",
            lis_result_sourcedid="modelstudent-assignment1",
        )
        lti_outcomes_client.record_result.assert_called_once_with(
            expected_outcome_params, score=pyramid_request.parsed_params["score"]
        )

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.parsed_params = {
            # Metadata provided by LMS for requests to LTI Outcomes Management
            # service.
            "lis_outcome_service_url": "https://hypothesis.shinylms.com/outcomes",
            "lis_result_sourcedid": "modelstudent-assignment1",
            "score": 0.5,
        }
        return pyramid_request


@pytest.fixture(autouse=True)
def lti_outcomes_client(pyramid_config):
    svc = mock.create_autospec(LTIOutcomesClient, instance=True, spec_set=True)
    pyramid_config.register_service(svc, name="lti_outcomes_client")
    return svc
