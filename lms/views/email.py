import logging

from pyramid.httpexceptions import HTTPFound
from pyramid.security import remember
from pyramid.view import forbidden_view_config, view_config, view_defaults

from lms.security import Permissions
from lms.services import EmailPreferencesService
from lms.services.exceptions import ExpiredJWTError, InvalidJWTError

LOG = logging.getLogger(__name__)


@view_config(
    route_name="email.unsubscribe",
    request_method="GET",
    request_param="token",
    renderer="lms:templates/email/expired_link.html.jinja2",
)
def unsubscribe(request):
    """Unsubscribe the email and tag combination encoded in token."""
    try:
        request.find_service(EmailPreferencesService).unsubscribe(
            request.params["token"]
        )
    except (InvalidJWTError, ExpiredJWTError):
        LOG.exception("Invalid unsubscribe token")
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


@forbidden_view_config(
    route_name="email.preferences",
    request_method="GET",
    request_param="token",
    renderer="lms:templates/email/expired_link.html.jinja2",
)
def forbidden(_request):
    return {}


@view_defaults(permission=Permissions.EMAIL_PREFERENCES)
class EmailPreferencesViews:
    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.email_preferences_service = request.find_service(EmailPreferencesService)

    @view_config(
        route_name="email.preferences",
        request_method="GET",
        request_param="token",
    )
    def preferences_redirect(self):
        # The token has already been verified by the security policy, so we can
        # just go right ahead with the redirect.
        return HTTPFound(
            location=self.request.route_url("email.preferences"),
            # Set a cookie to keep the user logged in even though we're
            # removing the authentication token from the URL.
            headers=remember(self.request, self.request.authenticated_userid),
        )

    @view_config(
        route_name="email.preferences",
        request_method="GET",
        renderer="lms:templates/email/preferences.html.jinja2",
    )
    def preferences(self):
        self.context.js_config.enable_email_notifications_mode(
            email_notifications_preferences=self.email_preferences_service.get_preferences(
                self.request.authenticated_userid
            )
        )
        return {}

    @view_config(
        route_name="email.preferences",
        request_method="POST",
    )
    def set_preferences(self):
        self.email_preferences_service.set_preferences(
            self.request.authenticated_userid,
            {
                key: self.request.params.get(key) == "on"
                for key in self.email_preferences_service.DAY_KEYS
            },
        )
        return HTTPFound(location=self.request.route_url("email.preferences"))
