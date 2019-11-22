from behave import when
from h_matchers import Any
from webtest import TestApp

from tests.bdd.step_context import StepContext
from tests.bdd.steps.the_response import WebTestResponse


class TheApp(StepContext):
    context_key = "the_app"

    def __init__(self, app, **kwargs):
        self.app = TestApp(app)

    def send_request(self, request):
        # Translate requests.request into a test app call

        method = getattr(self.app, request.method.lower())

        return method(
            url=request.url,
            headers=request.headers,
            params=request.data,
            status=Any.int(),
        )


@when("I send the request to the app")
def sent_request_to_app(context):
    request = context.the_request.request
    response = context.the_app.send_request(request)

    WebTestResponse.register(context, response=response)
