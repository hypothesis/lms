from h_pyramid_sentry import report_exception
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config

from lms.services import EmailUnsubscribeService
from lms.services.exceptions import ExpiredJWTError, InvalidJWTError


@view_config(
    route_name="email.unsubscribe",
    request_method="GET",
    renderer="lms:templates/error.html.jinja2",
)
def unsubscribe(request):
    """Unsubscribe the email and tag combination encoded in token."""
    try:
        request.find_service(EmailUnsubscribeService).unsubscribe(
            request.matchdict["token"]
        )
    except (InvalidJWTError, ExpiredJWTError):
        request.override_renderer = "lms:templates/error.html.jinja2"
        # We want to see this in  sentry
        report_exception()
        return {"message": "Something went wrong while unsubscribing."}

    return HTTPFound(location=request.route_url("email.unsubscribed"))


@view_config(
    route_name="email.unsubscribed",
    request_method="GET",
    renderer="lms:templates/error.html.jinja2",
)
def unsubscribed(_request):
    """Render a message after a succefull email unsubscribe."""
    return {"message": "You've been unsubscribed"}
