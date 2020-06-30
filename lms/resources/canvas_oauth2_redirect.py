from pyramid.security import Allow

from lms.resources._js_config import JSConfig


class CanvasOAuth2RedirectResource:
    """Resource for the Canvas OAuth 2 redirect popup."""

    __acl__ = [(Allow, "lti_user", "canvas_api")]

    def __init__(self, request):
        self._js_config = None
        self._request = request

    @property
    def js_config(self):
        if not self._request.exception:
            # The normal views do not need to configure the frontend, only
            # the exception views.
            return None

        if not self._js_config:
            self._js_config = JSConfig(self, self._request)
        return self._js_config
