from unittest.mock import Mock, sentinel

import pytest
import xmltodict
from h_matchers import Any

from lms.services.exceptions import ExternalRequestError, StudentNotInCourse
from lms.services.lti_grading._v11 import LTI11GradingService
from tests import factories


@pytest.mark.usefixtures("oauth1_service", "http_service")
class TestLTI11GradingService:
    def test_read_result(self, svc, respond_with, http_service):
        respond_with(GradingResponse(score=0.95))

        result = svc.read_result(sentinel.grading_id)

        assert self.sent_pox_body(http_service) == {
            "readResultRequest": {
                "resultRecord": {"sourcedGUID": {"sourcedId": "sentinel.grading_id"}}
            }
        }
        assert result.score == 0.95
        assert result.comment is None

    @pytest.mark.parametrize("score", [None, "", "not-a-float"])
    def test_read_result_returns_none_if_score_not_a_float(
        self, svc, respond_with, score
    ):
        respond_with(GradingResponse(score=score))

        assert svc.read_result(sentinel.grading_id).score is None

    def test_read_result_returns_none_if_no_score(self, svc, respond_with):
        response = GradingResponse()
        response.result_response["result"]["resultScore"].pop("textString")
        respond_with(response)

        assert svc.read_result(sentinel.grading_id).score is None

    def test_methods_raises_StudentNotInCourse(self, svc, respond_with):
        response = GradingResponse(
            status_code="failure",
            description="Incorrect sourcedId: sentinel.grading_id",
        )
        respond_with(response)

        with pytest.raises(StudentNotInCourse):
            svc.read_result(sentinel.grading_id)

    @pytest.mark.usefixtures("with_response")
    @pytest.mark.parametrize(
        "score,score_payload",
        (
            (0.5, {"result": {"resultScore": {"language": "en", "textString": "0.5"}}}),
            (0, {"result": {"resultScore": {"language": "en", "textString": "0"}}}),
            (None, {}),
        ),
    )
    def test_record_result(self, svc, score, http_service, score_payload):
        svc.record_result(sentinel.grading_id, score=score)

        assert self.sent_pox_body(http_service) == {
            "replaceResultRequest": {
                "resultRecord": {
                    "sourcedGUID": {"sourcedId": "sentinel.grading_id"},
                    **score_payload,
                }
            }
        }

    @pytest.mark.usefixtures("with_response")
    def test_sync_grade(self, svc, http_service, application_instance, db_session):
        lms_user = factories.LMSUser()
        assignment = factories.Assignment()
        lti_role = factories.LTIRole()
        db_session.flush()
        membership = factories.LMSUserAssignmentMembership(
            lms_user_id=lms_user.id,
            assignment_id=assignment.id,
            lti_role_id=lti_role.id,
            lti_v11_lis_result_sourcedid="LIS",
        )

        svc.sync_grade(application_instance, assignment, None, lms_user, 0.5)

        assert self.sent_pox_body(http_service) == {
            "replaceResultRequest": {
                "resultRecord": {
                    "sourcedGUID": {
                        "sourcedId": membership.lti_v11_lis_result_sourcedid
                    },
                    "result": {"resultScore": {"language": "en", "textString": "0.5"}},
                }
            }
        }

    @pytest.mark.usefixtures("with_response")
    def test_record_result_calls_hook(self, svc, http_service):
        my_hook = Mock(return_value={"my_dict": 1})

        svc.record_result(sentinel.grading_id, score=1.5, pre_record_hook=my_hook)

        my_hook.assert_called_once_with(request_body=Any.dict(), score=1.5)
        assert self.sent_pox_body(http_service) == {
            "replaceResultRequest": {"my_dict": "1"}
        }

    @pytest.mark.usefixtures("with_response")
    def test_methods_make_valid_post_requests(
        self, svc_method, http_service, oauth1_service
    ):
        svc_method(sentinel.grading_id)

        http_service.post.assert_called_once_with(
            url=sentinel.service_url,
            data=Any.string.matching(r"<\?xml"),
            headers={"Content-Type": "application/xml"},
            auth=oauth1_service.get_client.return_value,
        )

        assert self.sent_body(http_service)["imsx_POXEnvelopeRequest"][
            "imsx_POXHeader"
        ] == {
            "imsx_POXRequestHeaderInfo": {
                "imsx_version": "V1.0",
                "imsx_messageIdentifier": "999999123",
            }
        }

    def test_methods_fail_if_the_third_party_request_fails(
        self, svc_method, http_service
    ):
        http_service.post.side_effect = ExternalRequestError

        with pytest.raises(ExternalRequestError):
            svc_method(sentinel.grading_id)

    def test_methods_fail_if_body_not_xml(self, svc_method, http_service):
        http_service.post.return_value = factories.requests.Response(
            status_code=200, body='{"not":"xml"}', content_type="application/json"
        )

        with pytest.raises(
            ExternalRequestError,
            match="Unable to parse XML response from LTI Outcomes service",
        ):
            svc_method(sentinel.grading_id)

    def test_methods_fail_if_no_status(self, svc_method, respond_with):
        response = GradingResponse()
        response.header_info.pop("imsx_statusInfo")
        respond_with(response)

        with pytest.raises(
            ExternalRequestError, match="Malformed LTI outcome response"
        ):
            svc_method(sentinel.grading_id)

    def test_methods_fail_if_response_is_malformed(self, svc_method, respond_with):
        # "imsx_POXEnvelopeResponse" is the expected key. This erroneous value
        # is inspired by Blackbaud.
        respond_with({"imsx_POXEnvelopeRequest": {"etc": ...}})

        with pytest.raises(
            ExternalRequestError, match="Malformed LTI outcome response"
        ):
            svc_method(sentinel.grading_id)

    def test_methods_fail_if_status_is_not_success(self, svc_method, respond_with):
        respond_with(GradingResponse(status_code="failure"))

        with pytest.raises(
            ExternalRequestError,
            match="<imsx_description>An error occurred.</imsx_description>",
        ):
            svc_method(sentinel.grading_id)

    def test_methods_fail_with_no_description_returned(self, svc_method, respond_with):
        response = GradingResponse(status_code="failure")
        response.header_info["imsx_statusInfo"].pop("imsx_description")
        respond_with(response)

        with pytest.raises(ExternalRequestError, match="LTI outcome request failed"):
            svc_method(sentinel.grading_id)

    @classmethod
    def sent_body(cls, http_service):
        return xmltodict.parse(http_service.post.call_args[1]["data"])

    @classmethod
    def sent_pox_body(cls, http_service):
        return cls.sent_body(http_service)["imsx_POXEnvelopeRequest"]["imsx_POXBody"]

    @pytest.fixture
    def with_response(self, respond_with):
        respond_with(GradingResponse())

    @pytest.fixture
    def respond_with(self, http_service):
        def respond_with(response):
            http_service.post.return_value = factories.requests.Response(
                status_code=200,
                raw=xmltodict.unparse(response),
                content_type="application/xml",
            )

        return respond_with

    @pytest.fixture(params=["record_result", "read_result"])
    def svc_method(self, svc, request):
        return getattr(svc, request.param)

    @pytest.fixture
    def svc(self, oauth1_service, http_service, application_instance, db_session):
        return LTI11GradingService(
            db_session,
            sentinel.service_url,
            http_service,
            oauth1_service,
            application_instance,
        )


class GradingResponse(dict):
    """An LTI grading response dict with convenience accessors."""

    def __init__(
        self, status_code="success", score=0.92, description="An error occurred."
    ):
        super().__init__(
            {
                "imsx_POXEnvelopeResponse": {
                    "@xmlns": "http://www.imsglobal.org/services/ltiv1p1/xsd/imsoms_v1p0",
                    "imsx_POXHeader": {
                        "imsx_POXResponseHeaderInfo": {
                            "imsx_version": "V1.0",
                            "imsx_messageIdentifier": 1313355158804,
                            "imsx_statusInfo": {
                                "imsx_codeMajor": status_code,
                                "imsx_severity": "status",
                                "imsx_messageRefIdentifier": "999999123",
                                "imsx_operationRefIdentifier": "readResult",
                                "imsx_description": description,
                            },
                        }
                    },
                    "imsx_POXBody": {
                        "readResultResponse": {
                            "result": {
                                "resultScore": {"language": "en", "textString": score}
                            }
                        }
                    },
                }
            }
        )

    @property
    def header_info(self):
        return self["imsx_POXEnvelopeResponse"]["imsx_POXHeader"][
            "imsx_POXResponseHeaderInfo"
        ]

    @property
    def result_response(self):
        return self["imsx_POXEnvelopeResponse"]["imsx_POXBody"]["readResultResponse"]
