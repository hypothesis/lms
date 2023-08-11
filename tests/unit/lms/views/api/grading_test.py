import datetime
from datetime import timezone
from unittest.mock import patch, sentinel

import pytest
from h_matchers import Any

from lms.services.lti_grading.interface import GradingResult
from lms.views.api.grading import CanvasPreRecordHook, GradingViews

pytestmark = pytest.mark.usefixtures("lti_grading_service")


class TestRecordCanvasSpeedgraderSubmission:
    GRADING_ID = "lis_result_sourcedid"

    def test_it_passes_correct_params_to_read_current_score(
        self, pyramid_request, lti_grading_service
    ):
        GradingViews(pyramid_request).record_canvas_speedgrader_submission()

        lti_grading_service.read_result.assert_called_once_with(self.GRADING_ID)

    def test_it_does_not_record_result_if_score_already_exists(
        self, pyramid_request, lti_grading_service
    ):
        lti_grading_service.read_result.return_value = 0.5

        GradingViews(pyramid_request).record_canvas_speedgrader_submission()

        lti_grading_service.record_result.assert_not_called()

    def test_it_passes_the_callback_if_there_is_no_score(
        self, pyramid_request, lti_grading_service, LTIEvent
    ):
        lti_grading_service.read_result.return_value = None

        GradingViews(pyramid_request).record_canvas_speedgrader_submission()

        lti_grading_service.record_result.assert_called_once_with(
            self.GRADING_ID,
            pre_record_hook=Any.instance_of(CanvasPreRecordHook),
            # lti_launch_url=expected_launch_url,
            # submitted_at=datetime.datetime(2001, 1, 1, tzinfo=timezone.utc),
        )
        LTIEvent.assert_called_once_with(
            request=pyramid_request, type=LTIEvent.Type.SUBMISSION
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
        }
        return pyramid_request


class TestCanvasPreRecordHook:
    @pytest.mark.parametrize(
        "parsed_params,url_params",
        [
            [{"document_url": "https://example.com"}, {"url": "https://example.com"}],
            [
                {"vitalsource_book_id": "BOOK_ID", "vitalsource_cfi": "CFI"},
                {"vitalsource_book": "true", "book_id": "BOOK_ID", "cfi": "CFI"},
            ],
            [
                {"canvas_file_id": "file123"},
                {"canvas_file": "true", "file_id": "file123"},
            ],
        ],
    )
    def test_get_speedgrader_launch_url(
        self, parsed_params, url_params, pyramid_request
    ):
        pyramid_request.parsed_params.update(parsed_params)

        launch_url = CanvasPreRecordHook(pyramid_request).get_speedgrader_launch_url()

        assert launch_url == Any.url.with_path("/lti_launches").with_query(
            dict(
                url_params,
                focused_user="h_username",
                learner_canvas_user_id="learner_canvas_user_id",
            )
        )

    @pytest.mark.parametrize(
        "submitted_at", (datetime.datetime(2022, 2, 3, tzinfo=timezone.utc), None)
    )
    def test_it_v11(self, hook, submitted_at, get_speedgrader_launch_url):
        hook.request.parsed_params["submitted_at"] = submitted_at

        result = hook(score=None, request_body={"resultRecord": {}})

        assert result == {
            "resultRecord": {
                "result": {
                    "resultData": {
                        "ltiLaunchUrl": get_speedgrader_launch_url.return_value
                    }
                }
            },
            "submissionDetails": {
                "submittedAt": submitted_at or hook.DEFAULT_SUBMISSION_DATE
            },
        }

    @pytest.mark.parametrize(
        "submitted_at", (datetime.datetime(2022, 2, 3, tzinfo=timezone.utc), None)
    )
    def test_it_v13(self, hook, submitted_at, get_speedgrader_launch_url):
        hook.request.parsed_params["submitted_at"] = submitted_at

        result = hook(score=None, request_body={})

        assert result == {
            "https://canvas.instructure.com/lti/submission": {
                "submission_type": "basic_lti_launch",
                "submission_data": get_speedgrader_launch_url.return_value,
                "submitted_at": (
                    submitted_at or hook.DEFAULT_SUBMISSION_DATE
                ).isoformat(),
            }
        }

    @pytest.fixture
    def hook(self, pyramid_request):
        return CanvasPreRecordHook(pyramid_request)

    @pytest.fixture
    def get_speedgrader_launch_url(self, hook):
        with patch.object(hook, "get_speedgrader_launch_url", autospec=True) as patched:
            yield patched

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.parsed_params = {
            "h_username": "h_username",
            "learner_canvas_user_id": "learner_canvas_user_id",
        }
        return pyramid_request


class TestReadResult:
    def test_it_proxies_to_read_result(self, pyramid_request, lti_grading_service):
        GradingViews(pyramid_request).read_result()

        lti_grading_service.read_result.assert_called_once_with(
            "modelstudent-assignment1"
        )

    def test_it_returns_current_result(self, pyramid_request, lti_grading_service):
        lti_grading_service.read_result.return_value = GradingResult(
            score=sentinel.score, comment=sentinel.comment
        )

        current_score = GradingViews(pyramid_request).read_result()

        assert current_score == {
            "currentScore": sentinel.score,
            "comment": sentinel.comment,
        }

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
    @pytest.mark.parametrize(
        "score,expected",
        [
            (0.7000000000000001, 0.7),
            (0.7123000000000001, 0.7123),
            (0.000000000000001, 0),
        ],
    )
    def test_it_records_result(
        self, pyramid_request, lti_grading_service, score, expected, LTIEvent
    ):
        pyramid_request.parsed_params["score"] = score
        GradingViews(pyramid_request).record_result()

        lti_grading_service.record_result.assert_called_once_with(
            "modelstudent-assignment1", score=expected
        )
        LTIEvent.assert_called_once_with(
            request=pyramid_request,
            type=LTIEvent.Type.GRADE,
            data={"student_user_id": sentinel.student_user_id, "score": expected},
        )

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.parsed_params = {
            # Metadata provided by LMS for requests to LTI Outcomes Management
            # service.
            "lis_outcome_service_url": "https://hypothesis.shinylms.com/outcomes",
            "lis_result_sourcedid": "modelstudent-assignment1",
            "score": 0.5,
            "student_user_id": sentinel.student_user_id,
        }
        return pyramid_request


@pytest.fixture
def LTIEvent(patch):
    return patch("lms.views.api.grading.LTIEvent")
