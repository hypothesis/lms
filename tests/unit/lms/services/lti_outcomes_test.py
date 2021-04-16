from collections import OrderedDict
from unittest.mock import Mock

import httpretty
import pytest
import xmltodict
from h_matchers import Any
from requests import RequestException

from lms.services.exceptions import LTIOutcomesAPIError
from lms.services.lti_outcomes import LTIOutcomesClient

pytestmark = pytest.mark.usefixtures("oauth1_service")


class TestLTIOutcomesClient:
    SERVICE_URL = "http://example.com/service_url"
    GRADING_ID = "lis_result_sourcedid"

    def test_read_result_sends_expected_request(self, svc, respond_with):
        respond_with(score=0.95)

        svc.read_result(self.GRADING_ID)

        self.assert_sent_header_ok()

        result_record = self.sent_pox_body()["readResultRequest"]["resultRecord"]
        sourced_id = result_record["sourcedGUID"]["sourcedId"]
        assert sourced_id == self.GRADING_ID

    def test_read_result_returns_float_score(self, svc, respond_with):
        respond_with(score=0.95)

        score = svc.read_result(self.GRADING_ID)

        assert score == 0.95

    def test_read_result_returns_none_if_no_score(self, svc, respond_with):
        respond_with(include_score=None)

        score = svc.read_result(self.GRADING_ID)

        assert score is None

    @pytest.mark.parametrize("score_text", [None, "", "not-a-float"])
    def test_read_result_returns_none_if_score_not_a_float(
        self, svc, respond_with, score_text
    ):
        respond_with(score=score_text)

        score = svc.read_result(self.GRADING_ID)

        assert score is None

    @pytest.mark.usefixtures("response")
    def test_record_result_sends_sourcedid(self, svc):
        svc.record_result(self.GRADING_ID)

        self.assert_sent_header_ok()

        result_record = self.sent_pox_body()["replaceResultRequest"]["resultRecord"]
        sourced_id = result_record["sourcedGUID"]["sourcedId"]

        assert sourced_id == self.GRADING_ID

    @pytest.mark.usefixtures("response")
    @pytest.mark.parametrize(
        "score_provided,score_in_record",
        [
            (0.5, "0.5"),
            (0, "0"),  # test the zero value
        ],
    )
    def test_record_result_sends_score(self, svc, score_provided, score_in_record):
        svc.record_result(self.GRADING_ID, score=score_provided)

        result_record = self.sent_pox_body()["replaceResultRequest"]["resultRecord"]
        score = result_record["result"]["resultScore"]["textString"]

        assert score == score_in_record

    @pytest.mark.usefixtures("response")
    def test_record_result_calls_hook(self, svc):
        my_hook = Mock(return_value={"my_dict": 1})

        svc.record_result(self.GRADING_ID, score=1.5, pre_record_hook=my_hook)

        my_hook.assert_called_once_with(request_body=Any.dict(), score=1.5)
        assert self.sent_pox_body()["replaceResultRequest"] == OrderedDict(
            {"my_dict": "1"}
        )

    @pytest.mark.parametrize("hook_result", [None, [], "foo"])
    def test_record_result_requires_dict_result(self, svc, hook_result):
        with pytest.raises(TypeError):
            svc.record_result(
                self.GRADING_ID, pre_record_hook=lambda *args, **kwargs: hook_result
            )

    def test_it_signs_request_with_oauth1(self, svc, requests, oauth1_service):
        requests.post.side_effect = OSError()

        # We don't care if this actually does anything afterwards, so just
        # fail here so we can see how we were called
        with pytest.raises(OSError):
            svc.record_result(self.GRADING_ID)

        requests.post.assert_called_with(
            url=Any(),
            data=Any(),
            headers=Any(),
            auth=oauth1_service.get_client.return_value,
            timeout=Any(),
        )

    def test_requests_fail_if_http_status_is_error(self, svc, respond_with):
        respond_with(status=400)

        with pytest.raises(LTIOutcomesAPIError):
            svc.read_result(self.GRADING_ID)

    def test_requests_fail_if_body_not_xml(self, svc):
        httpretty.register_uri(
            httpretty.POST,
            self.SERVICE_URL,
            body='{"not":"xml"}',
            content_type="application/json",
            priority=1,
        )
        with pytest.raises(
            LTIOutcomesAPIError,
            match="Unable to parse XML response from LTI Outcomes service",
        ):
            svc.read_result(self.GRADING_ID)

    def test_requests_fail_if_no_status(self, svc, respond_with):
        respond_with(include_status=False)
        with pytest.raises(LTIOutcomesAPIError, match="Malformed LTI outcome response"):
            svc.read_result(self.GRADING_ID)

    def test_requests_fail_if_response_is_malformed(self, svc, respond_with):
        respond_with(malformed=True)

        with pytest.raises(LTIOutcomesAPIError, match="Malformed LTI outcome response"):
            svc.read_result(self.GRADING_ID)

    def test_requests_fail_if_status_is_not_success(self, svc, respond_with):
        respond_with(status_code="failure")

        # LTI outcome request failed
        with pytest.raises(
            LTIOutcomesAPIError,
            match="<imsx_description>An error occurred.</imsx_description>",
        ):
            svc.read_result(self.GRADING_ID)

    def test_requests_fail_and_no_description_returned(self, svc, respond_with):
        respond_with(status_code="failure", include_description=False)

        # imsx_description is missing
        with pytest.raises(LTIOutcomesAPIError, match="LTI outcome request failed"):
            svc.read_result(self.GRADING_ID)

    def test_it_gracefully_handles_RequestException(self, requests, svc):
        requests.post.side_effect = RequestException

        with pytest.raises(
            LTIOutcomesAPIError, match="Error calling LTI Outcomes service"
        ):
            svc.read_result(self.GRADING_ID)

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
    def make_response(
        cls, score, include_score, include_status, status_code, include_description
    ):
        header_info = {"imsx_version": "V1.0", "imsx_messageIdentifier": 1313355158804}

        if include_status:
            header_info["imsx_statusInfo"] = {
                "imsx_codeMajor": status_code,
                "imsx_severity": "status",
                "imsx_messageRefIdentifier": "999999123",
                "imsx_operationRefIdentifier": "readResult",
            }
            if include_description:
                header_info["imsx_statusInfo"][
                    "imsx_description"
                ] = "An error occurred."

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

    @classmethod
    def make_malformed_response(cls):
        return xmltodict.unparse(
            {
                # "imsx_POXEnvelopeResponse" is the expected key. This erroneous value is inspired
                # by Blackbaud.
                "imsx_POXEnvelopeRequest": {
                    "@xmlns": "http://www.imsglobal.org/services/ltiv1p1/xsd/imsoms_v1p0",
                    "imsx_POXHeader": {},
                    "imsx_POXBody": {},
                }
            }
        )

    @pytest.fixture
    def response(self, respond_with):
        respond_with()

    @pytest.fixture
    def respond_with(self):
        def configure(
            score=None,
            include_score=True,
            include_status=True,
            status_code="success",
            status=200,
            malformed=False,
            include_description=True,
        ):
            response_body = None

            if malformed:
                response_body = self.make_malformed_response()
            else:
                response_body = self.make_response(
                    score,
                    include_score,
                    include_status,
                    status_code,
                    include_description,
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
    def svc(self, pyramid_request):
        return LTIOutcomesClient({}, pyramid_request)

    @pytest.fixture
    def requests(self, patch):
        return patch("lms.services.lti_outcomes.requests")
