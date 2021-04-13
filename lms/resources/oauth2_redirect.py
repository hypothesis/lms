from lms.resources._js_config import JSConfig


class OAuth2RedirectResource:
    """Resource for the OAuth 2 redirect popup."""

    def __init__(self, request):
        # The frontend config is only used by the exception view, but it is OK
        # to set `js_config` unconditionally because the normal view replaces
        # the frontend scripts with one that just closes the window.
        self.js_config = JSConfig(self, request)
