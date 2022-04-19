from datetime import datetime, timezone
from xml.parsers.expat import ExpatError

import xmltodict

from lms.services import LTIAHTTPService
from lms.services.exceptions import ExternalRequestError

__all__ = ["LTIOutcomesClient"]


class LTIOutcomesClient:
    """
    Service for sending grades back to the LMS.

    See:
         LTI1.1 Outcomes https://www.imsglobal.org/specs/ltiomv1p0/specification.
         LTI1.3 Assignment and Grade Services https://www.imsglobal.org/spec/lti-ags/v2p0
    """

    LTIA_SCOPES = [
        "https://purl.imsglobal.org/spec/lti-ags/scope/lineitem",
        "https://purl.imsglobal.org/spec/lti-ags/scope/result.readonly",
        "https://purl.imsglobal.org/spec/lti-ags/scope/score",
    ]

    def __init__(  # pylint:disable=too-many-arguments
        self, oauth1_service, http_service, ltia_service, grading_url, lti_version
    ):
        self.oauth1_service = oauth1_service
        self.http_service = http_service
        self.ltia_service = ltia_service

        self.service_url = grading_url
        self.lti_version = lti_version

    def read_result(self, lis_result_sourcedid=None):
        if self.lti_version == "1.3.0":
            return self._read_result_lti_v13(lis_result_sourcedid)

        return self._read_result_lti_v11(lis_result_sourcedid)

    def record_result(self, lis_result_sourcedid, score=None, pre_record_hook=None):
        if self.lti_version == "1.3.0":
            return self._record_result_lti_v13(lis_result_sourcedid, score=score)

        return self._record_result_lti_v11(
            lis_result_sourcedid, score=score, pre_record_hook=pre_record_hook
        )

    def _read_result_lti_v13(self, lis_result_sourcedid):
        try:
            response = self.ltia_service.request(
                self.LTIA_SCOPES,
                "GET",
                self.service_url + "/results",
                params={"user_id": lis_result_sourcedid},
                headers={"Accept": "application/vnd.ims.lis.v2.resultcontainer+json"},
            )
        except ExternalRequestError as err:
            if err.status_code == 404:
                return None
            raise

        results = response.json()
        if not results:
            return None

        return results[-1]["resultScore"] / results[-1]["resultMaximum"]

    def _read_result_lti_v11(self, lis_result_sourcedid):
        """
        Return the last-submitted score for a given submission.

        :param lis_result_sourcedid: The submission id
        :return: The last-submitted score or `None` if no score has been
                 submitted.
        """

        result = self._send_request_lti_v11(
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

    def _record_result_lti_v11(
        self, lis_result_sourcedid, score=None, pre_record_hook=None
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

        :raise TypeError: if the given pre_record_hook returns a non-dict
        """

        request = {"resultRecord": {"sourcedGUID": {"sourcedId": lis_result_sourcedid}}}

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

    def _record_result_lti_v13(self, lis_result_sourcedid, score=None):

        return self.ltia_service.request(
            self.LTIA_SCOPES,
            "POST",
            self.service_url + "/scores",
            json={
                "scoreMaximum": 1,
                "scoreGiven": score,
                "userId": lis_result_sourcedid,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "activityProgress": "Completed",
                "gradingProgress": "FullyGraded",
            },
            headers={"Content-Type": "application/vnd.ims.lis.v2.lineitem+json"},
        )

    def _send_request_lti_v11(self, request_body):
        """
        Send a signed request to an LMS's Outcome Management Service endpoint.

        :arg request_body: The content to send as the POX body element of the
                           request

        :raise ExternalRequestError: if the request fails for any reason

        :return: The returned POX body element
        :rtype: dict
        """

        xml_body = xmltodict.unparse(self._pox_envelope(request_body))

        # Bind the variable so we can refer to it in the catch
        response = None

        try:
            response = self.http_service.post(
                url=self.service_url,
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


def factory(_context, request):
    return LTIOutcomesClient(
        request.find_service(name="oauth1"),
        request.find_service(name="http"),
        request.find_service(LTIAHTTPService),
        request.parsed_params["lis_outcome_service_url"],
        request.find_service(name="application_instance").get_current().lti_version,
    )
