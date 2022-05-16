from unittest.mock import sentinel
from urllib.parse import parse_qs, urlparse

import pytest

from lms.views.api.lti import LTIOutcomesViews, get_speedgrader_launch_url

pytestmark = pytest.mark.usefixtures("lti_grading_service")


class TestRecordCanvasSpeedgraderSubmission:
    GRADING_ID = "lis_result_sourcedid"

    def test_it_passes_correct_params_to_read_current_score(
        self, pyramid_request, lti_grading_service
    ):
        LTIOutcomesViews(pyramid_request).record_canvas_speedgrader_submission()

        lti_grading_service.read_result.assert_called_once_with(self.GRADING_ID)

    def test_it_does_not_record_result_if_score_already_exists(
        self, pyramid_request, lti_grading_service
    ):
        lti_grading_service.read_result.return_value = 0.5

        LTIOutcomesViews(pyramid_request).record_canvas_speedgrader_submission()

        lti_grading_service.record_result.assert_not_called()

    def test_it_passes_canvas_extensions(self, pyramid_request, lti_grading_service):
        lti_grading_service.read_result.return_value = None

        LTIOutcomesViews(pyramid_request).record_canvas_speedgrader_submission()

        lti_grading_service.record_result.assert_called_once_with(
            self.GRADING_ID,
            canvas_lti_launch_url=get_speedgrader_launch_url(pyramid_request),
            canvas_submitted_at=sentinel.submitted_at,
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
            "lis_result_sourcedid": self.GRADING_ID,
            "submitted_at": sentinel.submitted_at,
            "learner_canvas_user_id": "learner_canvas_user_id",
        }
        return pyramid_request


class TestGetSpeedGraderLaunchURL:
    @pytest.mark.parametrize(
        "parsed_params,url_params",
        [
            [{"document_url": "https://example.com"}, {"url": ["https://example.com"]}],
            [
                {"vitalsource_book_id": "BOOK_ID", "vitalsource_cfi": "CFI"},
                {"vitalsource_book": ["true"], "book_id": ["BOOK_ID"], "cfi": ["CFI"]},
            ],
            [
                {"canvas_file_id": "file123"},
                {"canvas_file": ["true"], "file_id": ["file123"]},
            ],
        ],
    )
    def test_it(self, pyramid_request, parsed_params, url_params):
        pyramid_request.parsed_params.update(parsed_params)

        url = get_speedgrader_launch_url(pyramid_request)

        assert url.startswith("http://example.com/lti_launches?")
        query_string = parse_qs(urlparse(url).query)
        assert query_string == dict(
            url_params,
            focused_user=["h_username"],
            learner_canvas_user_id=["learner_canvas_user_id"],
        )

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.parsed_params = {
            "h_username": "h_username",
            "learner_canvas_user_id": "learner_canvas_user_id",
        }
        return pyramid_request


class TestReadResult:
    def test_it_proxies_to_read_result(self, pyramid_request, lti_grading_service):
        LTIOutcomesViews(pyramid_request).read_result()

        lti_grading_service.read_result.assert_called_once_with(
            "modelstudent-assignment1"
        )

    def test_it_returns_current_score(self, pyramid_request, lti_grading_service):
        lti_grading_service.read_result.return_value = 0.5

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
    def test_it_records_result(self, pyramid_request, lti_grading_service):
        LTIOutcomesViews(pyramid_request).record_result()

        lti_grading_service.record_result.assert_called_once_with(
            "modelstudent-assignment1", score=pyramid_request.parsed_params["score"]
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
