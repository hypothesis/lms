import datetime
from xml.etree import ElementTree

import httpretty
import pytest
from jinja2 import Template
from requests import RequestException

from lms.services.exceptions import LTIOutcomesAPIError
from lms.services.lti_outcomes import LTIOutcomesClient, LTIOutcomesRequestParams

LTI_OUTCOME_RESPONSE_TEMPLATE = Template(
    """<?xml version="1.0" encoding="UTF-8"?>
<imsx_POXEnvelopeResponse
  xmlns="http://www.imsglobal.org/services/ltiv1p1/xsd/imsoms_v1p0"
>
  <imsx_POXHeader>
    <imsx_POXResponseHeaderInfo>
      <imsx_version>V1.0</imsx_version>
      <imsx_messageIdentifier>1313355158804</imsx_messageIdentifier>
      {% if not exclude_status %}
      <imsx_statusInfo>
        <imsx_codeMajor>{{ status_code|default('success') }}</imsx_codeMajor>
        <imsx_severity>status</imsx_severity>
        <imsx_description>Result read</imsx_description>
        <imsx_messageRefIdentifier>999999123</imsx_messageRefIdentifier>
        <imsx_operationRefIdentifier>readResult</imsx_operationRefIdentifier>
      </imsx_statusInfo>
      {% endif %}
    </imsx_POXResponseHeaderInfo>
  </imsx_POXHeader>
  <imsx_POXBody>
    <readResultResponse>
      <result>
        <resultScore>
          <language>en</language>
          {% if not exclude_score %}
          <textString>{{ score }}</textString>
          {% endif %}
        </resultScore>
      </result>
    </readResultResponse>
  </imsx_POXBody>
</imsx_POXEnvelopeResponse>"""
)


class TestLTIOutcomesClient:
    def test_read_result_sends_expected_request(
        self, lti_outcomes_params, lti_outcomes_svc, configure_response, request_xml
    ):
        configure_response({"score": 0.95})

        lti_outcomes_svc.read_result(lti_outcomes_params)

        xml = request_xml()
        self.check_header(xml)
        sourcedid = self.element_text(
            xml,
            [
                "imsx_POXBody",
                "readResultRequest",
                "resultRecord",
                "sourcedGUID",
                "sourcedId",
            ],
        )
        assert sourcedid == lti_outcomes_params.lis_result_sourcedid

    def test_read_result_returns_float_score(
        self, lti_outcomes_params, lti_outcomes_svc, configure_response
    ):
        configure_response({"score": 0.95})

        score = lti_outcomes_svc.read_result(lti_outcomes_params)

        assert score == 0.95

    def test_read_result_returns_none_if_no_score(
        self, lti_outcomes_params, lti_outcomes_svc, configure_response
    ):
        configure_response({"exclude_score": True})

        score = lti_outcomes_svc.read_result(lti_outcomes_params)

        assert score is None

    @pytest.mark.parametrize("score_text", ["", "not-a-float"])
    def test_read_result_returns_none_if_score_not_a_float(
        self, lti_outcomes_params, lti_outcomes_svc, configure_response, score_text
    ):
        configure_response({"score": score_text})

        score = lti_outcomes_svc.read_result(lti_outcomes_params)

        assert score is None

    def test_record_result_sends_sourcedid(
        self, lti_outcomes_params, lti_outcomes_svc, configure_response, request_xml
    ):
        configure_response({})

        lti_outcomes_svc.record_result(lti_outcomes_params)
        xml = request_xml()

        self.check_header(xml)
        sourcedid = self.element_text(
            xml, ["replaceResultRequest", "resultRecord", "sourcedGUID", "sourcedId"]
        )
        assert sourcedid == lti_outcomes_params.lis_result_sourcedid

    def test_record_result_sends_score(
        self,
        lti_outcomes_params,
        lti_outcomes_svc,
        configure_response,
        record_result_request_fields,
    ):
        configure_response({})

        lti_outcomes_svc.record_result(lti_outcomes_params, score=0.5)

        assert record_result_request_fields() == {"score": "0.5"}

    def test_record_result_sends_launch_url(
        self,
        lti_outcomes_params,
        lti_outcomes_svc,
        configure_response,
        record_result_request_fields,
    ):
        configure_response({})
        lti_launch_url = "https://lms.hypothes.is/lti_launches"

        lti_outcomes_svc.record_result(
            lti_outcomes_params, lti_launch_url=lti_launch_url
        )

        assert record_result_request_fields() == {"lti_launch_url": lti_launch_url}

    def test_record_result_sends_submitted_at(
        self,
        lti_outcomes_params,
        lti_outcomes_svc,
        configure_response,
        record_result_request_fields,
    ):
        configure_response({})
        submitted_at = datetime.datetime(2010, 1, 1)

        lti_outcomes_svc.record_result(lti_outcomes_params, submitted_at=submitted_at)

        assert record_result_request_fields() == {
            "submitted_at": submitted_at.isoformat()
        }

    def test_it_signs_request_with_oauth1(
        self, lti_outcomes_params, lti_outcomes_svc, configure_response
    ):
        configure_response({})

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
        configure_response({}, status=400)

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
        configure_response({"exclude_status": True})
        with pytest.raises(LTIOutcomesAPIError):
            lti_outcomes_svc.read_result(lti_outcomes_params)

    def test_requests_fail_if_status_is_not_success(
        self, lti_outcomes_params, lti_outcomes_svc, configure_response
    ):
        configure_response({"status_code": "failure"})

        with pytest.raises(LTIOutcomesAPIError):
            lti_outcomes_svc.read_result(lti_outcomes_params)

    def test_it_gracefully_handles_RequestException(
        self, requests, lti_outcomes_svc, lti_outcomes_params
    ):
        requests.post.side_effect = RequestException

        with pytest.raises(LTIOutcomesAPIError):
            lti_outcomes_svc.read_result(lti_outcomes_params)

    @pytest.fixture
    def request_xml(self):
        """Return parsed XML of last request."""

        def xml():
            request = httpretty.last_request()
            return ElementTree.fromstring(request.body)

        return xml

    @pytest.fixture
    def record_result_request_fields(self, request_xml):
        """Return a dict of fields that were set in the last-sent `replaceResult` request."""

        def get_fields():
            xml = request_xml()
            fields = {}
            score = self.element_text(
                xml,
                [
                    "replaceResultRequest",
                    "resultRecord",
                    "result",
                    "resultScore",
                    "textString",
                ],
            )
            if score is not None:
                fields["score"] = score

            lti_launch_url = self.element_text(
                xml,
                [
                    "replaceResultRequest",
                    "resultRecord",
                    "result",
                    "resultData",
                    "ltiLaunchUrl",
                ],
            )
            if lti_launch_url is not None:
                fields["lti_launch_url"] = lti_launch_url

            submitted_at = self.element_text(
                xml, ["replaceResultRequest", "submissionDetails", "submittedAt"]
            )
            if submitted_at is not None:
                fields["submitted_at"] = submitted_at

            return fields

        return get_fields

    @pytest.fixture
    def configure_response(self, lti_outcomes_params):
        def configure(template_params, status=200):
            response_body = LTI_OUTCOME_RESPONSE_TEMPLATE.render(**template_params)
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

    @classmethod
    def element_text(cls, xml, path):
        element = LTIOutcomesClient.find_element(xml, path)
        if element is None:
            return None
        return element.text

    @classmethod
    def check_header(cls, xml):
        """Check standard header fields of an LTI Outcomes Management request body."""
        assert (
            cls.element_text(
                xml,
                [
                    "imsx_POXHeader",
                    "imsx_POXRequestHeaderInfo",
                    "imsx_messageIdentifier",
                ],
            )
            == "999999123"
        )
