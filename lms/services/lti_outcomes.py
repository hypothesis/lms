from typing import NamedTuple
from xml.etree import ElementTree

import requests
from jinja2 import Template
from requests import RequestException
from requests_oauthlib import OAuth1

from lms.services.exceptions import LTIOutcomesAPIError

__all__ = ["LTIOutcomesClient", "LTIOutcomesRequestParams"]

LTI_OUTCOME_SERVICE_XML_NS = "http://www.imsglobal.org/services/ltiv1p1/xsd/imsoms_v1p0"

# Envelope for LTI Outcome Service requests sent to the LMS
#
# See https://www.imsglobal.org/specs/ltiomv1p0/specification for specs for all
# messages.
#
# nb. To be a valid XML document it is important that the template has no
# whitespace at the start.
LTI_OUTCOME_REQUEST_TEMPLATE = Template(
    """<?xml version="1.0" encoding="UTF-8"?>
<imsx_POXEnvelopeRequest xmlns="http://www.imsglobal.org/services/ltiv1p1/xsd/imsoms_v1p0">
  <imsx_POXHeader>
    <imsx_POXRequestHeaderInfo>
      <imsx_version>V1.0</imsx_version>
      <imsx_messageIdentifier>999999123</imsx_messageIdentifier>
    </imsx_POXRequestHeaderInfo>
  </imsx_POXHeader>
  <imsx_POXBody>
    {{ body }}
  </imsx_POXBody>
</imsx_POXEnvelopeRequest>
"""
)

# Template for a `replaceResult` XML message to send to the LMS.
REPLACE_RESULT_REQUEST_TEMPLATE = Template(
    """
<replaceResultRequest>
  <resultRecord>
    <sourcedGUID>
      <sourcedId>{{ lis_result_sourcedid | e }}</sourcedId>
    </sourcedGUID>
    <result>
      {% if score %}
      <resultScore>
        <language>en</language>
        <textString>{{ score | e }}</textString>
      </resultScore>
      {% endif %}
      {% if lti_launch_url %}
      <resultData>
        <ltiLaunchUrl>{{ lti_launch_url | e }}</ltiLaunchUrl>
      </resultData>
      {% endif %}
    </result>
  </resultRecord>
  {% if submitted_at %}
  <submissionDetails>
    <submittedAt>{{ submitted_at.isoformat() }}</submittedAt>
  </submissionDetails>
  {% endif %}
</replaceResultRequest>
"""
)

# Template for a `readResult` XML message to send to the LMS.
READ_RESULT_REQUEST_TEMPLATE = Template(
    """
<readResultRequest>
  <resultRecord>
    <sourcedGUID>
      <sourcedId>{{ lis_result_sourcedid | e }}</sourcedId>
    </sourcedGUID>
  </resultRecord>
</readResultRequest>
"""
)


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

    def __init__(self, _context, request):
        pass

    def read_result(self, outcomes_request_params):  # pylint:disable=no-self-use
        """
        Return the last-submitted score for a given submission.

        :return: The last-submitted score or `None` if no score has been submitted.
        """
        body = READ_RESULT_REQUEST_TEMPLATE.render(
            lis_result_sourcedid=outcomes_request_params.lis_result_sourcedid
        )

        result = _send_request(outcomes_request_params, body)

        try:
            score = find_element(
                result, ["readResultResponse", "result", "resultScore", "textString"]
            )
            if score is None:
                return None
            return float(score.text)
        except (ValueError, TypeError):
            return None

    def record_result(  # pylint:disable=no-self-use
        self,
        outcomes_request_params,
        score=None,
        lti_launch_url=None,
        submitted_at=None,
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
        body = REPLACE_RESULT_REQUEST_TEMPLATE.render(
            lis_result_sourcedid=outcomes_request_params.lis_result_sourcedid,
            score=score,
            lti_launch_url=lti_launch_url,
            submitted_at=submitted_at,
        )

        _send_request(outcomes_request_params, body)


def _send_request(outcomes_request_params, pox_body):
    """
    Send a signed request to an LMS's Outcome Management Service endpoint.

    :arg pox_body: The content of the `imsx_POXBody` element in the request
    :return: Parsed XML response
    :rtype: ElementTree.Element
    """

    xml_body = LTI_OUTCOME_REQUEST_TEMPLATE.render(body=pox_body)

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

    status = find_element(xml, ["imsx_statusInfo", "imsx_codeMajor"])
    if status is None:
        raise LTIOutcomesAPIError("Failed to read status from LTI outcome response")

    if status.text != "success":
        raise LTIOutcomesAPIError("LTI outcome request failed")

    return xml


def find_element(xml_element, path):
    """Extract element from LTI Outcomes Management XML response."""
    xml_ns = LTI_OUTCOME_SERVICE_XML_NS
    xpath = "/".join([f"{{{xml_ns}}}{name}" for name in path])
    return xml_element.find(f".//{xpath}")
