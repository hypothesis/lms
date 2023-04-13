import logging

from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config

from lms.services import EmailUnsubscribeService
from lms.services.exceptions import ExpiredJWTError, InvalidJWTError

LOG = logging.getLogger(__name__)


@view_config(
    route_name="email.unsubscribe", request_method="GET", request_param="token"
)
def unsubscribe(request):
    """Unsubscribe the email and tag combination encoded in token."""
    try:
        request.find_service(EmailUnsubscribeService).unsubscribe(
            request.params["token"]
        )
    except (InvalidJWTError, ExpiredJWTError):
        LOG.exception("Invalid unsubscribe token")
        request.override_renderer = "lms:templates/email/unsubscribe_error.html.jinja2"
        return {}

    return HTTPFound(location=request.route_url("email.unsubscribed"))


@view_config(
    route_name="email.unsubscribed",
    request_method="GET",
    renderer="lms:templates/email/unsubscribed.html.jinja2",
)
def unsubscribed(_request):
    """Render a message after a successful email unsubscribe."""
    return {}
