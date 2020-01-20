from xml.parsers.expat import ExpatError

import requests
import xmltodict
from requests import RequestException

from lms.services.exceptions import LTIOutcomesAPIError

__all__ = ["LTIOutcomesClient"]


class LTIOutcomesClient:
    """
    Service for making requests to an LMS's Outcomes Management endpoint.

    See https://www.imsglobal.org/specs/ltiomv1p0/specification.
    """

    def __init__(self, _context, request):
        self.oauth1_service = request.find_service(name="oauth1")
        self.service_url = request.parsed_params["lis_outcome_service_url"]

    def read_result(self, lis_result_sourcedid):  # pylint:disable=no-self-use
        """
        Return the last-submitted score for a given submission.

        :param lis_result_sourcedid: The submission id
        :return: The last-submitted score or `None` if no score has been
                 submitted.
        """

        result = self._send_request(
            {
                "readResultRequest": {
                    "resultRecord": {"sourcedGUID": {"sourcedId": lis_result_sourcedid}}
                }
            }
        )

        try:
            return float(
                result["readResultResponse"]["result"]["resultScore"]["textString"]
            )
        except (TypeError, KeyError, ValueError):
            return None

    def record_result(  # pylint:disable=no-self-use
        self, lis_result_sourcedid, score=None, pre_record_hook=None,
    ):
        """
        Set the score or content URL for a student submission to an assignment.

        This method also accepts an optional callable hook which will be passed
        the `score` and the `request_body` which it can modify and must return.
        This allows support for extensions (or custom replacements) to the
        standard LTI outcomes body.

        :param lis_result_sourcedid: The submission id
        :param score:
            Float value between 0 and 1.0.
            Defined as required by the LTI spec but is optional in Canvas if
            an `lti_launch_url` is set.
        :param pre_record_hook: Hook to allow modification of the request
        """

        request = {"resultRecord": {"sourcedGUID": {"sourcedId": lis_result_sourcedid}}}

        if score:
            request["resultRecord"]["result"] = {
                "resultScore": {"language": "en", "textString": score}
            }

        if pre_record_hook:
            request = pre_record_hook(score=score, request_body=request)

            if not isinstance(request, dict):
                raise TypeError(
                    "The pre-record hook must return the request body as a dict"
                )

        self._send_request({"replaceResultRequest": request})

    def _send_request(self, request_body):
        """
        Send a signed request to an LMS's Outcome Management Service endpoint.

        :arg request_body: The content to send as the POX body element of the
                           request
        :return: The returned POX body element
        :rtype: dict
        """

        xml_body = xmltodict.unparse(self._pox_envelope(request_body))

        # Bind the variable so we can refer to it in the catch
        response = None

        try:
            response = requests.post(
                url=self.service_url,
                data=xml_body,
                headers={"Content-Type": "application/xml"},
                auth=self.oauth1_service.get_client(),
            )

            # Raise an exception if the status is bad
            response.raise_for_status()

        except RequestException as err:
            raise LTIOutcomesAPIError(
                "Error calling LTI Outcomes service", response
            ) from err

        try:
            data = xmltodict.parse(response.text)
        except ExpatError as e:
            raise LTIOutcomesAPIError(
                "Unable to parse XML response from LTI Outcomes service", response
            ) from e

        return self._get_body(data)

    @classmethod
    def _get_body(cls, data):
        """Return the POX body element, checking for errors."""

        try:
            body = data["imsx_POXEnvelopeResponse"]["imsx_POXBody"]
            header = data["imsx_POXEnvelopeResponse"]["imsx_POXHeader"]
            status = header["imsx_POXResponseHeaderInfo"]["imsx_statusInfo"][
                "imsx_codeMajor"
            ]

        except KeyError as e:
            raise LTIOutcomesAPIError("Malformed LTI outcome response") from e

        if status != "success":
            raise LTIOutcomesAPIError("LTI outcome request failed")

        return body

    @staticmethod
    def _pox_envelope(body):
        """
        Return ``body`` wrapped in an imsx_POXEnvelopeRequest envelope.

        Return an xmltodict-format XML dict - an XML document represented as
        a dict, suitable for converting into an XML string by passing it to
        ``xmltodict.unparse()``.

        The returned dict renders to an ``<imsx_POXEnvelopeRequest>`` document
        with the given ``body`` as the contents of the ``<imsx_POXBody>`` tag.

        :rtype: dict
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
