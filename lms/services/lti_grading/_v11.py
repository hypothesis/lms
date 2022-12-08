from dataclasses import dataclass
from enum import Enum
from xml.parsers.expat import ExpatError

import xmltodict
from requests import Response

from lms.services.exceptions import ExternalRequestError
from lms.services.http import HTTPService
from lms.services.lti_grading.exceptions import UnknownGradingStudent
from lms.services.lti_grading.interface import LTIGradingService
from lms.services.oauth1 import OAuth1Service


class _StatusCode(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    UNSUPPORTED = "unsupported"


@dataclass
class LTIOutcomesMessage:
    body: dict
    header: dict
    status: _StatusCode

    _response: Response

    @classmethod
    def from_response(cls, response):
        try:
            data = xmltodict.parse(response.text)
        except ExpatError as err:
            raise ExternalRequestError(
                "Unable to parse XML response from LTI Outcomes service", response
            ) from err

        try:
            header = data["imsx_POXEnvelopeResponse"]["imsx_POXHeader"]
            return cls(
                body=data["imsx_POXEnvelopeResponse"]["imsx_POXBody"],
                header=header,
                status=header["imsx_POXResponseHeaderInfo"]["imsx_statusInfo"][
                    "imsx_codeMajor"
                ],
                _response=response,
            )
        except KeyError as err:
            raise ExternalRequestError(
                "Malformed LTI outcome response", response=response
            ) from err

    def raise_for_status(self):
        if self.status != _StatusCode.SUCCESS:
            raise ExternalRequestError(
                message="LTI outcome request failed", response=self._response
            )


# pylint:disable=abstract-method
class LTI11GradingService(LTIGradingService):
    #  See: LTI1.1 Outcomes https://www.imsglobal.org/specs/ltiomv1p0/specification
    def __init__(
        self, line_item_url, http_service: HTTPService, oauth1_service: OAuth1Service
    ):
        super().__init__(line_item_url, None)
        self.http_service = http_service
        self.oauth1_service = oauth1_service

    def read_result(self, grading_id):
        result = self._send_request(
            {
                "readResultRequest": {
                    "resultRecord": {"sourcedGUID": {"sourcedId": grading_id}}
                }
            }
        )
        if result.status == _StatusCode.FAILURE:
            if (
                result.header.get("imsx_POXResponseHeaderInfo", {})
                .get("imsx_statusInfo", {})
                .get("imsx_description", "")
                .startswith("Incorrect sourcedId")
            ):
                raise UnknownGradingStudent(
                    "Unable to fetch grade. Is the student still in the course mate?"
                )

        try:
            return float(
                result.body["readResultResponse"]["result"]["resultScore"]["textString"]
            )
        except (TypeError, KeyError, ValueError) as err:
            return None

    def record_result(self, grading_id, score=None, pre_record_hook=None):
        request = {"resultRecord": {"sourcedGUID": {"sourcedId": grading_id}}}

        if score is not None:
            request["resultRecord"]["result"] = {
                "resultScore": {"language": "en", "textString": score}
            }

        if pre_record_hook:
            request = pre_record_hook(score=score, request_body=request)

        lti_outcomes_message = self._send_request({"replaceResultRequest": request})
        lti_outcomes_message.raise_for_status()

    def _send_request(self, request_body) -> LTIOutcomesMessage:
        """
        Send a signed request to an LMS's Outcome Management Service endpoint.

        :arg request_body: The content to send as the POX body element of the
                           request

        :raise ExternalRequestError: if the request fails for any reason

        :return: The returned POX body element
        """
        xml_body = xmltodict.unparse(self._pox_envelope(request_body))

        try:
            response = self.http_service.post(
                url=self.line_item_url,
                data=xml_body,
                headers={"Content-Type": "application/xml"},
                auth=self.oauth1_service.get_client(),
            )
        except ExternalRequestError as err:
            err.message = "Error calling LTI Outcomes service"
            raise

        return LTIOutcomesMessage.from_response(response)

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
