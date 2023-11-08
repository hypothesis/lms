import logging

from pyramid.httpexceptions import HTTPFound
from pyramid.security import remember
from pyramid.view import view_config, view_defaults
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound

from lms.models import UserPreferences

LOG = logging.getLogger(__name__)

WEEK_DAYS = (
    "sunday",
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
)


@view_defaults(
    request_method="GET",
    permission="email.settings",
    renderer="lms:templates/email/settings.html.jinja2",
)
class EmailSettingsViews:
    def __init__(self, request):
        self.request = request

    @view_config(route_name="email.settings", request_param="token")
    def settings_redirect(self):
        return self._redirect_to_settings_page()

    @view_config(route_name="email.unsubscribe", request_param="token")
    def unsubscribe(self):
        self.set_preferences({day: False for day in WEEK_DAYS})
        self.request.session.flash("You have been unsubscribed")
        return self._redirect_to_settings_page()

    @view_config(route_name="email.settings")
    def settings(self):
        return {
            "preferences": self.get_preferences().get("instructor_email_digest", {})
        }

    @view_config(route_name="email.settings", request_method="POST")
    def save_settings(self):
        self.set_preferences(
            {day: self.request.params.get(day) == "on" for day in WEEK_DAYS}
        )
        return self._redirect_to_settings_page()

    def get_preferences(self):
        h_userid = self.request.authenticated_userid

        try:
            preferences = self.request.db.scalars(
                select(UserPreferences).where(UserPreferences.h_userid == h_userid)
            ).one()
        except NoResultFound:
            preferences = UserPreferences(h_userid=h_userid, preferences={})
            self.request.db.add(preferences)

        preferences.preferences.setdefault(
            "instructor_email_digest", {day: True for day in WEEK_DAYS}
        )

        return preferences.preferences

    def set_preferences(self, new_preferences):
        preferences = self.get_preferences()
        preferences["instructor_email_digest"].update(new_preferences)
        preferences.changed()

    def _redirect_to_settings_page(self):
        return HTTPFound(
            location=self.request.route_url("email.settings"),
            headers=remember(self.request, self.request.authenticated_userid),
        )
