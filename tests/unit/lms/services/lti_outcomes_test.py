import datetime

import httpretty
import pytest
from requests import RequestException

from lms.logic.simple_xml import POX
from lms.services.exceptions import LTIOutcomesAPIError
from lms.services.lti_outcomes import LTIOutcomesClient, LTIOutcomesRequestParams


class TestLTIOutcomesClient:
    XML_NS = "http://www.imsglobal.org/services/ltiv1p1/xsd/imsoms_v1p0"

    READ_RESULT = "/n:imsx_POXBody/n:readResultRequest"
    REPLACE_RESULT = "/n:imsx_POXBody/n:replaceResultRequest/"

    def test_read_result_sends_expected_request(
        self, lti_outcomes_params, lti_outcomes_svc, configure_response
    ):
        configure_response(score=0.95)

        lti_outcomes_svc.read_result(lti_outcomes_params)

        self.assert_sent_header_ok()

        result_record = self.sent_pox_body()["readResultRequest"]["resultRecord"]
        sourced_id = result_record["sourcedGUID"]["sourcedId"]
        assert sourced_id == lti_outcomes_params.lis_result_sourcedid

    def test_read_result_returns_float_score(
        self, lti_outcomes_params, lti_outcomes_svc, configure_response
    ):
        configure_response(score=0.95)

        score = lti_outcomes_svc.read_result(lti_outcomes_params)

        assert score == 0.95

    def test_read_result_returns_none_if_no_score(
        self, lti_outcomes_params, lti_outcomes_svc, configure_response
    ):
        configure_response(score=None)

        score = lti_outcomes_svc.read_result(lti_outcomes_params)

        assert score is None

    @pytest.mark.parametrize("score_text", ["", "not-a-float"])
    def test_read_result_returns_none_if_score_not_a_float(
        self, lti_outcomes_params, lti_outcomes_svc, configure_response, score_text
    ):
        configure_response(score=score_text)

        score = lti_outcomes_svc.read_result(lti_outcomes_params)

        assert score is None

    def test_record_result_sends_sourcedid(
        self, lti_outcomes_params, lti_outcomes_svc, configure_response
    ):
        configure_response()

        lti_outcomes_svc.record_result(lti_outcomes_params)

        self.assert_sent_header_ok()

        result_record = self.sent_pox_body()["replaceResultRequest"]["resultRecord"]
        sourced_id = result_record["sourcedGUID"]["sourcedId"]

        assert sourced_id == lti_outcomes_params.lis_result_sourcedid

    def test_record_result_sends_score(
        self, lti_outcomes_params, lti_outcomes_svc, configure_response,
    ):
        configure_response()

        lti_outcomes_svc.record_result(lti_outcomes_params, score=0.5)

        result_record = self.sent_pox_body()["replaceResultRequest"]["resultRecord"]
        score = result_record["result"]["resultScore"]["textString"]

        assert score == "0.5"

    def test_record_result_sends_launch_url(
        self, lti_outcomes_params, lti_outcomes_svc, configure_response,
    ):
        configure_response()
        lti_launch_url = "https://lms.hypothes.is/lti_launches"

        lti_outcomes_svc.record_result(
            lti_outcomes_params, lti_launch_url=lti_launch_url
        )

        result_record = self.sent_pox_body()["replaceResultRequest"]["resultRecord"]
        found_launch_url = result_record["resultData"]["ltiLaunchUrl"]

        assert found_launch_url == lti_launch_url

    def test_record_result_sends_submitted_at(
        self, lti_outcomes_params, lti_outcomes_svc, configure_response,
    ):
        configure_response()
        submitted_at = datetime.datetime(2010, 1, 1)

        lti_outcomes_svc.record_result(lti_outcomes_params, submitted_at=submitted_at)

        found_submitted_at = self.sent_pox_body()["replaceResultRequest"][
            "submissionDetails"
        ]["submittedAt"]

        assert found_submitted_at == submitted_at.isoformat()

    def test_it_signs_request_with_oauth1(
        self, lti_outcomes_params, lti_outcomes_svc, configure_response
    ):
        configure_response()

        lti_outcomes_svc.record_result(lti_outcomes_params)

        request = httpretty.last_request()
        auth_header = request.headers["Authorization"]

        # nb. This currently doesn't verify the signature, it only checks that
        # one is present.
        assert auth_header.startswith("OAuth")
        assert 'oauth_version="1.0"' in auth_header
        assert 'oauth_consumer_key="lms_consumer_key"' in auth_header
        assert 'oauth_signature_method="HMAC-SHA1"' in auth_header
        assert "oauth_signature=" in auth_header

    def test_requests_fail_if_http_status_is_error(
        self, lti_outcomes_params, lti_outcomes_svc, configure_response
    ):
        configure_response(status=400)

        with pytest.raises(LTIOutcomesAPIError):
            lti_outcomes_svc.read_result(lti_outcomes_params)

    def test_requests_fail_if_body_not_xml(self, lti_outcomes_params, lti_outcomes_svc):
        httpretty.register_uri(
            httpretty.POST,
            lti_outcomes_params.lis_outcome_service_url,
            body='{"not":"xml"}',
            content_type="application/json",
            priority=1,
        )
        with pytest.raises(LTIOutcomesAPIError):
            lti_outcomes_svc.read_result(lti_outcomes_params)

    def test_requests_fail_if_no_status(
        self, lti_outcomes_params, lti_outcomes_svc, configure_response
    ):
        configure_response(include_status=False)
        with pytest.raises(LTIOutcomesAPIError):
            lti_outcomes_svc.read_result(lti_outcomes_params)

    def test_requests_fail_if_status_is_not_success(
        self, lti_outcomes_params, lti_outcomes_svc, configure_response
    ):
        configure_response(status_code="failure")

        with pytest.raises(LTIOutcomesAPIError):
            lti_outcomes_svc.read_result(lti_outcomes_params)

    def test_it_gracefully_handles_RequestException(
        self, requests, lti_outcomes_svc, lti_outcomes_params
    ):
        requests.post.side_effect = RequestException

        with pytest.raises(LTIOutcomesAPIError):
            lti_outcomes_svc.read_result(lti_outcomes_params)

    @classmethod
    def make_response(cls, score, include_status, status_code):
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
        if score:
            result_score["textString"] = score

        return POX.to_bytes(
            {
                "imsx_POXEnvelopeResponse": {
                    "_attrs": {"xmlns": cls.XML_NS},
                    "imsx_POXHeader": {"imsx_POXResponseHeaderInfo": header_info},
                    "imsx_POXBody": {
                        "readResultResponse": {"result": {"resultScore": result_score}}
                    },
                }
            }
        )

    @classmethod
    def sent_body(cls):
        return POX.to_dict(httpretty.last_request().body)

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

    @pytest.fixture
    def configure_response(self, lti_outcomes_params):
        def configure(
            score=None, include_status=True, status_code="success", status=200
        ):
            response_body = self.make_response(score, include_status, status_code)

            httpretty.register_uri(
                httpretty.POST,
                lti_outcomes_params.lis_outcome_service_url,
                body=response_body,
                content_type="application/xml",
                priority=1,
                status=status,
            )

        return configure

    @pytest.fixture
    def lti_outcomes_params(self):
        return LTIOutcomesRequestParams(
            consumer_key="lms_consumer_key",
            shared_secret="lms_shared_secret",
            lis_outcome_service_url="https://hypothesis.foolms.com/lti/outcomes",
            lis_result_sourcedid="modelstudent-assignment123",
        )

    @pytest.fixture
    def lti_outcomes_svc(self, pyramid_request):
        return LTIOutcomesClient({}, pyramid_request)

    @pytest.fixture
    def requests(self, patch):
        return patch("lms.services.lti_outcomes.requests")
