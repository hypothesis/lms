from typing import NamedTuple
from xml.etree import ElementTree

import requests
import xmltodict
from requests import RequestException
from requests_oauthlib import OAuth1

from lms.services.exceptions import LTIOutcomesAPIError

__all__ = ["LTIOutcomesClient", "LTIOutcomesRequestParams"]


class LTIOutcomesRequestParams(NamedTuple):
    """Common parameters used by all LTI Outcomes Management requests."""

    consumer_key: str
    """OAuth 1.0 consumer key used to sign the request."""

    shared_secret: str
    """OAuth 1.0 shared secret used to sign the request."""

    lis_outcome_service_url: str
    """URL to submit requests to, provided by the LMS during an LTI launch."""

    lis_result_sourcedid: str
    """
    Opaque identifier for a particular submission.

    This is provided by the LMS during an LTI launch and identifies the user
    and assignment that the launch refers to.
    """


class LTIOutcomesClient:
    """
    Service for making requests to an LMS's Outcomes Management endpoint.

    See https://www.imsglobal.org/specs/ltiomv1p0/specification.
    """

    XML_NS = "http://www.imsglobal.org/services/ltiv1p1/xsd/imsoms_v1p0"

    def __init__(self, _context, request):
        pass

    def read_result(self, outcomes_request_params):  # pylint:disable=no-self-use
        """
        Return the last-submitted score for a given submission.

        :return: The last-submitted score or `None` if no score has been submitted.
        """

        result = self._send_request(
            outcomes_request_params,
            request_body={
                "readResultRequest": {
                    "resultRecord": {
                        "sourcedGUID": {
                            "sourcedId": outcomes_request_params.lis_result_sourcedid
                        }
                    }
                }
            },
        )

        try:
            score = self.find_element(
                result, ["readResultResponse", "result", "resultScore", "textString"]
            )
            if score is None:
                return None
            return float(score.text)
        except (ValueError, TypeError):
            return None

    def record_result(  # pylint:disable=no-self-use
        self, outcomes_request_params, score=None, **kwargs,
    ):
        """
        Record a score or grading view launch URL for an assignment in the LMS.

        :arg score:
            Float value between 0 and 1.0.
            Defined as required by the LTI spec but is optional in Canvas if
            an `lti_launch_url` is set.
        :arg lti_launch_url:
            A URL where the student's work on this submission can be viewed.
            This is only used in Canvas.
        :arg submitted_at:
        :type datetime.datetime:
            A `datetime.datetime` that indicates when the submission was created.
            This is only used in Canvas and is displayed in the SpeedGrader
            as the submission date.
            If the submission date matches an existing submission then the
            existing submission is updated rather than creating a new submission.
        """

        request = {
            "resultRecord": {
                "sourcedGUID": {
                    "sourcedId": outcomes_request_params.lis_result_sourcedid
                }
            }
        }

        if score:
            request["resultRecord"]["result"] = {
                "resultScore": {"language": "en", "textString": score}
            }

        # Canvas specific adaptations
        self._canvas_request_modification(request, **kwargs)

        self._send_request(
            outcomes_request_params, request_body={"replaceResultRequest": request}
        )

    @classmethod
    def _canvas_request_modification(
        cls, request, lti_launch_url=None, submitted_at=None, **_
    ):

        if lti_launch_url:
            request["resultRecord"].setdefault("result", {})["resultData"] = {
                "ltiLaunchUrl": lti_launch_url
            }

        if submitted_at:
            request["submissionDetails"] = {"submittedAt": submitted_at.isoformat()}

    @classmethod
    def find_element(cls, xml_element, path):
        """Extract element from LTI Outcomes Management XML response."""
        xpath = "/".join([f"{{{cls.XML_NS}}}{name}" for name in path])

        return xml_element.find(f".//{xpath}")

    @classmethod
    def _send_request(cls, outcomes_request_params, request_body):
        """
        Send a signed request to an LMS's Outcome Management Service endpoint.

        :arg request_body: The content to send as the body element of the
                           request
        :return: Parsed XML response
        :rtype: ElementTree.Element
        """

        xml_body = xmltodict.unparse(cls._pox_wrapper(request_body))

        # Sign request using OAuth 1.0.
        oauth_client = OAuth1(
            client_key=outcomes_request_params.consumer_key,
            client_secret=outcomes_request_params.shared_secret,
            signature_method="HMAC-SHA1",
            signature_type="auth_header",
            # Include the body when signing the request, this defaults to `False`
            # for non-form encoded bodies.
            force_include_body=True,
        )

        try:
            response = None  # Bind the variable so we can refer to it in the catch
            response = requests.post(
                url=outcomes_request_params.lis_outcome_service_url,
                data=xml_body,
                headers={"Content-Type": "application/xml"},
                auth=oauth_client,
            )
            # The following will raise ``requests.exceptions.HTTPError`` if
            # there was an HTTP-related problem with the request. This exception
            # is a subclass of ``requests.exceptions.RequestError``.
            response.raise_for_status()
        except RequestException as err:
            # Handle any kind of ``RequestException``, be it an ``HTTPError`` or other
            # flavor of ``RequestException``.
            raise LTIOutcomesAPIError(
                "Error calling LTI Outcomes service", response
            ) from err

        # Parse response and check status code embedded in XML.
        try:
            xml = ElementTree.fromstring(response.text)
        except ElementTree.ParseError as err:
            raise LTIOutcomesAPIError(
                "Unable to parse XML response from LTI Outcomes service", response
            ) from err

        status = cls.find_element(xml, ["imsx_statusInfo", "imsx_codeMajor"])
        if status is None:
            raise LTIOutcomesAPIError("Failed to read status from LTI outcome response")

        if status.text != "success":
            raise LTIOutcomesAPIError("LTI outcome request failed")

        return xml

    @classmethod
    def _pox_wrapper(cls, body):
        """
        Envelope for LTI Outcome Service requests sent to the LMS.

        See https://www.imsglobal.org/specs/ltiomv1p0/specification for
        specs for all messages.
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
