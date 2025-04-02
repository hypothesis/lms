import logging

from pyramid.httpexceptions import HTTPFound
from pyramid.security import remember
from pyramid.view import forbidden_view_config, view_config, view_defaults

from lms.js_config_types import EmailPreferences
from lms.security import Permissions
from lms.services.email_preferences import EmailPreferencesService, EmailTypes

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

        self.email_preferences_service.unsubscribe(
            self.request.identity.h_userid, self.request.identity.tag
        )
        messages = {
            EmailTypes.INSTRUCTOR_DIGEST: "You've been unsubscribed from student annotation email notifications.",
            EmailTypes.MENTION: "You've been unsubscribed from mention emails.",
        }
        self.request.session.flash(
            messages[self.request.identity.tag], "email_preferences_result"
        )

        return HTTPFound(
            location=self.request.route_url("email.preferences"),
            # Set a cookie to keep the user logged in even though we're
            # removing the authentication token from the URL.
            headers=remember(self.request, self.request.authenticated_userid),
        )

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
        flash_messages = self.request.session.pop_flash("email_preferences_result")
        email_preferences = self.email_preferences_service.get_preferences(
            self.request.authenticated_userid
        )

        return {
            "jsConfig": {
                "mode": "email-preferences",
                "emailPreferences": EmailPreferences(
                    is_instructor=email_preferences.is_instructor,
                    selectedDays={
                        "mon": email_preferences.mon,
                        "tue": email_preferences.tue,
                        "wed": email_preferences.wed,
                        "thu": email_preferences.thu,
                        "fri": email_preferences.fri,
                        "sat": email_preferences.sat,
                        "sun": email_preferences.sun,
                    },
                    mention_email_feature_enabled=email_preferences.mention_email_feature_enabled,
                    mention_email_subscribed=email_preferences.mention_email_subscribed,
                    flashMessage=flash_messages[0] if flash_messages else None,
                ),
            }
        }

    @view_config(
        route_name="email.preferences",
        request_method="POST",
    )
    def set_preferences(self):
        params = self.request.params
        email_preferences = self.email_preferences_service.get_preferences(
            self.request.authenticated_userid
        )

        if email_preferences.is_instructor:
            email_preferences.mon = params.get("mon") == "on"
            email_preferences.tue = params.get("tue") == "on"
            email_preferences.wed = params.get("wed") == "on"
            email_preferences.thu = params.get("thu") == "on"
            email_preferences.fri = params.get("fri") == "on"
            email_preferences.sat = params.get("sat") == "on"
            email_preferences.sun = params.get("sun") == "on"

        if email_preferences.mention_email_feature_enabled:
            # Only set the mention_email_subscribed preference if the feature is enabled
            # This avoids setting it to False if the feature is not yet enabled
            email_preferences.mention_email_subscribed = (
                params.get("mention_email_subscribed") == "on"
            )

        self.email_preferences_service.set_preferences(email_preferences)
        self.request.session.flash("Preferences saved.", "email_preferences_result")
        return HTTPFound(location=self.request.route_url("email.preferences"))
