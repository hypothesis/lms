from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config, view_defaults

from lms.extensions.feature_flags._helpers import FeatureFlagsCookieHelper


@view_defaults(
    route_name="feature_flags_cookie_form",
    renderer="../_templates/cookie_form.html.jinja2",
)
class CookieFormViews:
    """A form for toggling feature flags in a cookie."""

    def __init__(self, request):
        self._cookie_helper = FeatureFlagsCookieHelper(request)
        self._request = request

    @view_config(request_method="GET")
    def get(self):
        """Render the feature flags cookie form page."""
        flags = self._cookie_helper.get_all()

        return {
            "flags": flags,
            "effective": {flag: self._request.feature(flag) for flag in flags.keys()},
        }

    @view_config(request_method="POST")
    def post(self):
        """Handle a feature flags cookie form submission."""
        response = HTTPFound(
            location=self._request.route_url("feature_flags_cookie_form")
        )
        self._cookie_helper.set_cookie(response)
        self._request.session.flash(
            "Feature flags saved in cookie ✔", "feature_flags", allow_duplicate=False
        )
        return response
