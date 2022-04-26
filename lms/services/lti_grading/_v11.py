from dataclasses import dataclass
from xml.parsers.expat import ExpatError

import xmltodict

from lms.services.exceptions import ExternalRequestError
from lms.services.http import HTTPService
from lms.services.lti_grading.interface import LTIGradingClient
from lms.services.oauth1 import OAuth1Service


@dataclass
class LTI11GradingClient(LTIGradingClient):
    #  See: LTI1.1 Outcomes https://www.imsglobal.org/specs/ltiomv1p0/specification

    http_service: HTTPService
    oauth1_service: OAuth1Service

    def read_result(self, grading_id):
        result = self._send_request_lti_v11(
            {
                "readResultRequest": {
                    "resultRecord": {"sourcedGUID": {"sourcedId": grading_id}}
                }
            }
        )

        try:
            return float(
                result["readResultResponse"]["result"]["resultScore"]["textString"]
            )
        except (TypeError, KeyError, ValueError):
            return None

    def record_result(self, grading_id, score=None, pre_record_hook=None):
        request = {"resultRecord": {"sourcedGUID": {"sourcedId": grading_id}}}

        if score is not None:
            request["resultRecord"]["result"] = {
                "resultScore": {"language": "en", "textString": score}
            }

        if pre_record_hook:
            request = pre_record_hook(score=score, request_body=request)

            if not isinstance(request, dict):
                raise TypeError(
                    "The pre-record hook must return the request body as a dict"
                )

        self._send_request_lti_v11({"replaceResultRequest": request})

    def _send_request_lti_v11(self, request_body) -> dict:
        """
        Send a signed request to an LMS's Outcome Management Service endpoint.
        """

        xml_body = xmltodict.unparse(self._pox_envelope(request_body))

        try:
            response = self.http_service.post(
                url=self.grading_url,
                data=xml_body,
                headers={"Content-Type": "application/xml"},
                auth=self.oauth1_service.get_client(),
            )
        except ExternalRequestError as err:
            err.message = "Error calling LTI Outcomes service"
            raise

        try:
            data = xmltodict.parse(response.text)
        except ExpatError as err:
            raise ExternalRequestError(
                "Unable to parse XML response from LTI Outcomes service", response
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
            raise ExternalRequestError("Malformed LTI outcome response") from err

        if status != "success":
            raise ExternalRequestError(message="LTI outcome request failed")

        return body

    @staticmethod
    def _pox_envelope(body):
        """Return ``body`` wrapped in an imsx_POXEnvelopeRequest envelope."""

        # This is an xmltodict-format XML dict
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
