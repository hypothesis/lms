from lms.resources._js_config import JSConfig


class DashboardResource:
    """Resource for the dashboards app."""

    def __init__(self, request):
        self.js_config = JSConfig(self, request)
