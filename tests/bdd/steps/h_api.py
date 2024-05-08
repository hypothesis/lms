import re

from h_matchers import Any
from httpretty import httpretty

from tests.bdd.step_context import StepContext


class HAPIContext(StepContext):
    context_key = "h_api"

    def do_setup(self):
        """Set up HTTPretty to intercept HTTP calls to the H API."""

        httpretty.reset()

        # Start interception
        httpretty.enable()

        # This is the URL we expect all H API calls to go to
        httpretty.register_uri(
            method=Any(),
            uri=re.compile(r"^https://h.example.com/.*"),
            body="",
        )

        # Catch URLs we aren't expecting or have failed to mock
        def error_response(request, uri, response_headers):  # noqa: ARG001
            raise NotImplementedError(f"Unexpected call to URL: {request.method} {uri}")

        httpretty.register_uri(method=Any(), uri=re.compile(".*"), body=error_response)

    def do_teardown(self):
        # Stop interception
        httpretty.disable()
