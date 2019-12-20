import datetime
from unittest import mock

import httpretty
import pytest
import xmltodict
from h_matchers import Any
from requests import RequestException

from lms.services.exceptions import LTIOutcomesAPIError
from lms.services.lti_outcomes import LTIOutcomesClient
from lms.services.oauth1 import OAuth1Service


class TestLTIOutcomesClient:
    SERVICE_URL = "http://example.com/service_url"
    GRADING_ID = "lis_result_sourcedid"

    def test_read_result_sends_expected_request(
        self, lti_outcomes_svc, configure_response
    ):
        configure_response(score=0.95)

        lti_outcomes_svc.read_result(self.GRADING_ID)

        self.assert_sent_header_ok()

        result_record = self.sent_pox_body()["readResultRequest"]["resultRecord"]
        sourced_id = result_record["sourcedGUID"]["sourcedId"]
        assert sourced_id == self.GRADING_ID

    def test_read_result_returns_float_score(
        self, lti_outcomes_svc, configure_response
    ):
        configure_response(score=0.95)

        score = lti_outcomes_svc.read_result(self.GRADING_ID)

        assert score == 0.95

    def test_read_result_returns_none_if_no_score(
        self, lti_outcomes_svc, configure_response
    ):
        configure_response(include_score=False)

        score = lti_outcomes_svc.read_result(self.GRADING_ID)

        assert score is None

    @pytest.mark.parametrize("score_text", [None, "", "not-a-float"])
    def test_read_result_returns_none_if_score_not_a_float(
        self, lti_outcomes_svc, configure_response, score_text
    ):
        configure_response(score=score_text)

        score = lti_outcomes_svc.read_result(self.GRADING_ID)

        assert score is None

    def test_record_result_sends_sourcedid(self, lti_outcomes_svc, configure_response):
        configure_response()

        lti_outcomes_svc.record_result(self.GRADING_ID)

        self.assert_sent_header_ok()

        result_record = self.sent_pox_body()["replaceResultRequest"]["resultRecord"]
        sourced_id = result_record["sourcedGUID"]["sourcedId"]

        assert sourced_id == self.GRADING_ID

    def test_record_result_sends_score(
        self, lti_outcomes_svc, configure_response,
    ):
        configure_response()

        lti_outcomes_svc.record_result(self.GRADING_ID, score=0.5)

        result_record = self.sent_pox_body()["replaceResultRequest"]["resultRecord"]
        score = result_record["result"]["resultScore"]["textString"]

        assert score == "0.5"

    def test_record_result_sends_launch_url(
        self, lti_outcomes_svc, configure_response,
    ):
        configure_response()
        lti_launch_url = "https://lms.hypothes.is/lti_launches"

        lti_outcomes_svc.record_result(self.GRADING_ID, lti_launch_url=lti_launch_url)

        result_record = self.sent_pox_body()["replaceResultRequest"]["resultRecord"]
        found_launch_url = result_record["result"]["resultData"]["ltiLaunchUrl"]

        assert found_launch_url == lti_launch_url

    def test_record_result_sends_submitted_at(
        self, lti_outcomes_svc, configure_response,
    ):
        configure_response()
        submitted_at = datetime.datetime(2010, 1, 1)

        lti_outcomes_svc.record_result(self.GRADING_ID, submitted_at=submitted_at)

        found_submitted_at = self.sent_pox_body()["replaceResultRequest"][
            "submissionDetails"
        ]["submittedAt"]

        assert found_submitted_at == submitted_at.isoformat()

    def test_it_signs_request_with_oauth1(self, lti_outcomes_svc, requests, oauth1_svc):
        requests.post.side_effect = OSError()

        # We don't care if this actually does anything afterwards, so just
        # fail here so we can see how we were called
        with pytest.raises(OSError):
            lti_outcomes_svc.record_result(self.GRADING_ID)

        requests.post.assert_called_with(
            url=Any(),
            data=Any(),
            headers=Any(),
            auth=oauth1_svc.get_client.return_value,
        )

    def test_requests_fail_if_http_status_is_error(
        self, lti_outcomes_svc, configure_response
    ):
        configure_response(status=400)

        with pytest.raises(LTIOutcomesAPIError):
            lti_outcomes_svc.read_result(self.GRADING_ID)

    def test_requests_fail_if_body_not_xml(self, lti_outcomes_svc):
        httpretty.register_uri(
            httpretty.POST,
            self.SERVICE_URL,
            body='{"not":"xml"}',
            content_type="application/json",
            priority=1,
        )
        with pytest.raises(LTIOutcomesAPIError):
            lti_outcomes_svc.read_result(self.GRADING_ID)

    def test_requests_fail_if_no_status(self, lti_outcomes_svc, configure_response):
        configure_response(include_status=False)
        with pytest.raises(LTIOutcomesAPIError):
            lti_outcomes_svc.read_result(self.GRADING_ID)

    def test_requests_fail_if_status_is_not_success(
        self, lti_outcomes_svc, configure_response
    ):
        configure_response(status_code="failure")

        with pytest.raises(LTIOutcomesAPIError):
            lti_outcomes_svc.read_result(self.GRADING_ID)

    def test_it_gracefully_handles_RequestException(self, requests, lti_outcomes_svc):
        requests.post.side_effect = RequestException

        with pytest.raises(LTIOutcomesAPIError):
            lti_outcomes_svc.read_result(self.GRADING_ID)

    @classmethod
    def sent_body(cls):
        return xmltodict.parse(httpretty.last_request().body)

    @classmethod
    def sent_pox_body(cls):
        return cls.sent_body()["imsx_POXEnvelopeRequest"]["imsx_POXBody"]

    @classmethod
    def assert_sent_header_ok(cls):
        """Check standard header fields of the request body."""

        body = cls.sent_body()

        header = body["imsx_POXEnvelopeRequest"]["imsx_POXHeader"]
        message_id = header["imsx_POXRequestHeaderInfo"]["imsx_messageIdentifier"]

        assert message_id == "999999123"

    @classmethod
    def make_response(cls, score, include_score, include_status, status_code):
        header_info = {"imsx_version": "V1.0", "imsx_messageIdentifier": 1313355158804}

        if include_status:
            header_info["imsx_statusInfo"] = {
                "imsx_codeMajor": status_code,
                "imsx_severity": "status",
                "imsx_description": "Result read",
                "imsx_messageRefIdentifier": "999999123",
                "imsx_operationRefIdentifier": "readResult",
            }

        result_score = {"language": "en"}
        if include_score:
            result_score["textString"] = score

        return xmltodict.unparse(
            {
                "imsx_POXEnvelopeResponse": {
                    "@xmlns": "http://www.imsglobal.org/services/ltiv1p1/xsd/imsoms_v1p0",
                    "imsx_POXHeader": {"imsx_POXResponseHeaderInfo": header_info},
                    "imsx_POXBody": {
                        "readResultResponse": {"result": {"resultScore": result_score}}
                    },
                }
            }
        )

    @pytest.fixture
    def configure_response(self):
        def configure(
            score=None,
            include_score=True,
            include_status=True,
            status_code="success",
            status=200,
        ):
            response_body = self.make_response(
                score, include_score, include_status, status_code
            )

            httpretty.register_uri(
                httpretty.POST,
                self.SERVICE_URL,
                body=response_body,
                content_type="application/xml",
                priority=1,
                status=status,
            )

        return configure

    @pytest.fixture(autouse=True)
    def pyramid_request(self, pyramid_request):
        pyramid_request.parsed_params = {"lis_outcome_service_url": self.SERVICE_URL}

        return pyramid_request

    @pytest.fixture
    def lti_outcomes_svc(self, pyramid_request):
        return LTIOutcomesClient({}, pyramid_request)

    @pytest.fixture(autouse=True)
    def oauth1_svc(self, pyramid_config):
        svc = mock.create_autospec(OAuth1Service, instance=True, spec_set=True)
        pyramid_config.register_service(svc, name="oauth1")
        return svc

    @pytest.fixture
    def requests(self, patch):
        return patch("lms.services.lti_outcomes.requests")
