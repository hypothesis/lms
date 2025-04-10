from xml.parsers.expat import ExpatError

import xmltodict
from sqlalchemy import select

from lms.models import ApplicationInstance, LMSUser, LMSUserAssignmentMembership
from lms.services.exceptions import ExternalRequestError, StudentNotInCourse
from lms.services.http import HTTPService
from lms.services.lti_grading.interface import GradingResult, LTIGradingService
from lms.services.oauth1 import OAuth1Service


class LTI11GradingService(LTIGradingService):
    #  See: LTI1.1 Outcomes https://www.imsglobal.org/specs/ltiomv1p0/specification
    def __init__(
        self,
        db,
        line_item_url,
        http_service: HTTPService,
        oauth1_service: OAuth1Service,
        application_instance: ApplicationInstance,
    ):
        super().__init__(line_item_url, None)
        self.db = db
        self.http_service = http_service
        self.oauth1_service = oauth1_service
        self.application_instance = application_instance

    def read_result(self, grading_id) -> GradingResult:
        result = GradingResult(score=None, comment=None)
        try:
            response = self._send_request(
                self.application_instance,
                self.line_item_url,
                {
                    "readResultRequest": {
                        "resultRecord": {"sourcedGUID": {"sourcedId": grading_id}}
                    }
                },
            )
        except ExternalRequestError as err:
            if err.response and "Incorrect sourcedId" in err.response.text:
                raise StudentNotInCourse(grading_id) from err

            raise

        try:  # noqa: SIM105
            result.score = float(
                response["readResultResponse"]["result"]["resultScore"]["textString"]
            )
        except (TypeError, KeyError, ValueError):
            pass

        return result

    def record_result(self, grading_id, score=None, pre_record_hook=None, comment=None):  # noqa: ARG002
        request = self._record_score_payload(score=score, user_grading_id=grading_id)
        if pre_record_hook:
            request = pre_record_hook(score=score, request_body=request)

        self._send_request(
            self.application_instance,
            self.line_item_url,
            {"replaceResultRequest": request},
        )

    def sync_grade(
        self,
        application_instance: ApplicationInstance,
        assignment,
        _grade_timestamp: str,
        lms_user: LMSUser,
        score: float,
    ):
        assignment_membership: LMSUserAssignmentMembership = self.db.scalars(
            select(LMSUserAssignmentMembership).where(
                LMSUserAssignmentMembership.lms_user_id == lms_user.id,
                LMSUserAssignmentMembership.assignment_id == assignment.id,
                LMSUserAssignmentMembership.lti_v11_lis_result_sourcedid.is_not(None),
            )
        ).first()
        assert (  # noqa: S101, PT018
            assignment_membership and assignment_membership.lti_v11_lis_result_sourcedid
        ), (
            "Trying to grade a student without a membership or membership without lti_v11_lis_result_sourcedid"
        )
        request = self._record_score_payload(
            score=score,
            user_grading_id=assignment_membership.lti_v11_lis_result_sourcedid,
        )
        self._send_request(
            application_instance,
            assignment.lis_outcome_service_url,
            {"replaceResultRequest": request},
        )

    def _send_request(
        self, application_instance, lis_outcome_service_url, request_body
    ) -> dict:
        """
        Send a signed request to an LMS's Outcome Management Service endpoint.

        :arg application_instance: ApplicationInstance used to sign this request
        :lis_outcome_service_url: URL of the grading service in the LMS
        :arg request_body: The content to send as the POX body element of the
                           request

        :raise ExternalRequestError: if the request fails for any reason

        :return: The returned POX body element
        """
        xml_body = xmltodict.unparse(self._pox_envelope(request_body))

        try:
            response = self.http_service.post(
                url=lis_outcome_service_url,
                data=xml_body,
                headers={"Content-Type": "application/xml"},
                auth=self.oauth1_service.get_client(application_instance),
            )
        except ExternalRequestError as err:
            err.message = "Error calling LTI Outcomes service"
            raise

        try:
            data = xmltodict.parse(response.text)
        except ExpatError as err:
            raise ExternalRequestError(  # noqa: TRY003
                "Unable to parse XML response from LTI Outcomes service",  # noqa: EM101
                response,
            ) from err

        try:
            return self._get_body(data)
        except ExternalRequestError as err:
            err.response = response
            raise

    @classmethod
    def _get_body(cls, data):
        """Return the POX body element, checking for errors."""

        try:
            body = data["imsx_POXEnvelopeResponse"]["imsx_POXBody"]
            header = data["imsx_POXEnvelopeResponse"]["imsx_POXHeader"]
            status = header["imsx_POXResponseHeaderInfo"]["imsx_statusInfo"][
                "imsx_codeMajor"
            ]
        except KeyError as err:
            raise ExternalRequestError("Malformed LTI outcome response") from err  # noqa: EM101, TRY003

        if status != "success":
            raise ExternalRequestError(message="LTI outcome request failed")

        return body

    @staticmethod
    def _pox_envelope(body) -> dict:
        """
        Return ``body`` wrapped in an imsx_POXEnvelopeRequest envelope.

        Return an xmltodict-format XML dict - an XML document represented as
        a dict, suitable for converting into an XML string by passing it to
        ``xmltodict.unparse()``.

        The returned dict renders to an ``<imsx_POXEnvelopeRequest>`` document
        with the given ``body`` as the contents of the ``<imsx_POXBody>`` tag.
        """
        return {
            "imsx_POXEnvelopeRequest": {
                "@xmlns": "http://www.imsglobal.org/services/ltiv1p1/xsd/imsoms_v1p0",
                "imsx_POXHeader": {
                    "imsx_POXRequestHeaderInfo": {
                        "imsx_version": "V1.0",
                        "imsx_messageIdentifier": "999999123",
                    }
                },
                "imsx_POXBody": body,
            }
        }

    @staticmethod
    def _record_score_payload(score: float | None, user_grading_id: str) -> dict:
        request: dict = {
            "resultRecord": {"sourcedGUID": {"sourcedId": user_grading_id}}
        }

        if score is not None:
            request["resultRecord"]["result"] = {
                "resultScore": {"language": "en", "textString": score}
            }

        return request
