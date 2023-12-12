import logging

from pyramid.httpexceptions import HTTPFound
from pyramid.security import remember
from pyramid.view import forbidden_view_config, view_config, view_defaults

from lms.security import Permissions
from lms.services import EmailPreferencesService, EmailPrefs

LOG = logging.getLogger(__name__)


@forbidden_view_config(
    route_name="email.preferences",
    request_method="GET",
    request_param="token",
    renderer="lms:templates/email/expired_link.html.jinja2",
)
@forbidden_view_config(
    route_name="email.unsubscribe",
    request_method="GET",
    request_param="token",
    renderer="lms:templates/email/expired_link.html.jinja2",
)
def forbidden(_request):
    return {}


@view_config(
    route_name="email.unsubscribed",
    request_method="GET",
    renderer="lms:templates/email/unsubscribed.html.jinja2",
)
def unsubscribed(_request):
    """Render a message after a successful email unsubscribe."""
    return {}


@view_defaults(permission=Permissions.EMAIL_PREFERENCES)
class EmailPreferencesViews:
    def __init__(self, request):
        self.request = request
        self.email_preferences_service = request.find_service(EmailPreferencesService)

    @view_config(
        route_name="email.unsubscribe",
        request_method="GET",
        request_param="token",
    )
    def unsubscribe(self):
        """Unsubscribe the email and tag combination encoded in token."""
        self.request.find_service(EmailPreferencesService).unsubscribe(
            self.request.identity.h_userid
        )

        return HTTPFound(location=self.request.route_url("email.unsubscribed"))

    @view_config(
        route_name="email.preferences",
        request_method="GET",
        renderer="lms:templates/email/preferences.html.jinja2",
    )
    def preferences(self):
        days = self.email_preferences_service.get_preferences(
            self.request.authenticated_userid
        ).days()
        self.request.response.headers = remember(
            self.request, self.request.authenticated_userid
        )

        return {
            "jsConfig": {
                "mode": "email-preferences",
                "emailPreferences": days,
            }
        }

    @view_config(
        route_name="email.preferences",
        request_method="POST",
    )
    def set_preferences(self):
        self.email_preferences_service.set_preferences(
            EmailPrefs(
                self.request.authenticated_userid,
                **{
                    key: self.request.params.get(key) == "on" for key in EmailPrefs.DAYS
                },
            )
        )
        return HTTPFound(location=self.request.route_url("email.preferences"))
