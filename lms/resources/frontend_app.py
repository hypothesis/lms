import functools

from lms.resources._js_config import JSConfig


class FrontendAppResource:
    """
    Generic context resource for views that serve frontend apps.

    Certain frontend apps (eg. LTI launches) will have more specific context
    resources.
    """

    def __init__(self, request):
        self._request = request

    @property
    @functools.lru_cache()
    def js_config(self):
        return JSConfig(self, self._request)
