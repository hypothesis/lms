from h_pyramid_sentry import report_exception
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config

from lms.services import EmailUnsubscribeService
from lms.services.exceptions import ExpiredJWTError, InvalidJWTError


@view_config(
    route_name="email.unsubscribe",
    request_method="GET",
    renderer="lms:templates/message.html.jinja2",
)
def unsubscribe(request):
    """Unsubscribe the email and tag combination encoded in token."""
    try:
        request.find_service(EmailUnsubscribeService).unsubscribe(
            request.matchdict["token"]
        )
    except (InvalidJWTError, ExpiredJWTError):
        # We want to see this in  sentry
        report_exception()
        return {
            "title": "Expired unsubscribe link",
            "message": """
                    <p>
                        It looks like the unsubscribe link that you clicked on was invalid or had expired.
                        Try clicking the unsubscribe link in a more recent email instead.
                    </p>
                    <p>
                        If the problem persists, you can
                         <a href="https://web.hypothes.is/get-help/?product=LMS_app" target="_blank" rel="noopener noreferrer">open a support ticket</a>
                         or visit our <a href="https://web.hypothes.is/help/" target="_blank" rel="noopener noreferrer">help documents</a>.
                    </p>
                    """,
        }

    return HTTPFound(location=request.route_url("email.unsubscribed"))


@view_config(
    route_name="email.unsubscribed",
    request_method="GET",
    renderer="lms:templates/message.html.jinja2",
)
def unsubscribed(_request):
    """Render a message after a successful email unsubscribe."""
    return {"title": "You've been unsubscribed"}
