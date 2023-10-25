from pyramid.httpexceptions import HTTPNotFound
from pyramid.request import Request
from pyramid.view import view_config
import logging

from lms.validation._lti_launch_params import LTILaunchSchema

LOG = logging.getLogger(__name__)


@view_config(request_method="POST", route_name="lti.launch", schema=LTILaunchSchema)
def launch(request):
    """LTI launch handler that dispatches to the right type of launch view depending of the message."""
    message_type = request.lti_params.get("lti_message_type")

    view_name = None

    if message_type in ("basic-lti-launch-request", "LtiResourceLinkRequest"):
        view_name = "lti_launches"

    elif message_type in ("ContentItemSelectionRequest", "LtiDeepLinkingRequest"):
        view_name = "content_item_selection"
    else:
        return HTTPNotFound()

    LOG.debug(
        "LTI launch view dispatch. Message type: %s. View: %s", message_type, view_name
    )
    sub_request = Request.blank(
        request.route_path(view_name, _query=request.GET),
        # We flag this request as coming from this endpoint
        POST=dict(request.POST, single_lti_endpoint=1),
    )

    # We don't want to use an HTTP redirect as that might interfere with LTI auth chain
    # Use a pyramid sub request to invoke the right view.
    # https://docs.pylonsproject.org/projects/pyramid/en/latest/narr/subrequest.html
    return request.invoke_subrequest(sub_request, use_tweens=True)
