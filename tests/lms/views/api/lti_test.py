import datetime
from datetime import timezone
from unittest import mock
from urllib.parse import urlencode

import pytest

from lms.views.api.lti import record_submission
from lms.services.lti_outcomes import LTIOutcomesClient, LTIOutcomesRequestParams
from lms.services.application_instance_getter import ApplicationInstanceGetter


class TestRecordSubmission:
    def test_it_passes_correct_params_to_read_current_score(
        self, pyramid_request, lti_outcomes_client
    ):
        record_submission(pyramid_request)

        lti_outcomes_client.read_result.assert_called_once_with(
            LTIOutcomesRequestParams(
                consumer_key="TEST_OAUTH_CONSUMER_KEY",
                shared_secret="oauth-secret",
                lis_outcome_service_url="https://hypothesis.shinylms.com/outcomes",
                lis_result_sourcedid="modelstudent-assignment1",
            )
        )

    def test_it_does_not_record_result_if_score_already_exists(
        self, pyramid_request, lti_outcomes_client
    ):
        lti_outcomes_client.read_result.return_value = 0.5

        record_submission(pyramid_request)

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

        record_submission(pyramid_request)

        expected_outcome_params = LTIOutcomesRequestParams(
            consumer_key="TEST_OAUTH_CONSUMER_KEY",
            shared_secret="oauth-secret",
            lis_outcome_service_url="https://hypothesis.shinylms.com/outcomes",
            lis_result_sourcedid="modelstudent-assignment1",
        )
        expected_submitted_at = datetime.datetime(2001, 1, 1, tzinfo=timezone.utc)
        expected_launch_url = "http://example.com/lti_launches?" + urlencode(
            {
                "focused_user": "user123",
                "assignment_oauth_consumer_key": "TEST_OAUTH_CONSUMER_KEY",
                **lti_launch_doc_params,
            }
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


@pytest.fixture(autouse=True)
def lti_outcomes_client(pyramid_config):
    svc = mock.create_autospec(LTIOutcomesClient, instance=True, spec_set=True)
    pyramid_config.register_service(svc, name="lti_outcomes_client")
    return svc


@pytest.fixture(autouse=True)
def ai_getter(pyramid_config):
    svc = mock.create_autospec(ApplicationInstanceGetter, instance=True, spec_set=True)

    def shared_secret(consumer_key):
        if consumer_key != "TEST_OAUTH_CONSUMER_KEY":
            raise Exception("Incorrect consumer key")
        return "oauth-secret"

    svc.shared_secret.side_effect = shared_secret
    pyramid_config.register_service(svc, name="ai_getter")
    return svc
