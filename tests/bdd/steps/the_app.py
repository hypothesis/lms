from behave import step
from h_matchers import Any
from webtest import TestApp

from tests.bdd.steps import WebTestResponse


class TheApp:
    def __init__(self, app):
        self.app = TestApp(app)

    @classmethod
    def register(cls, context, app):
        context.the_app = TheApp(app)

    def send_request(self, request):
        # Translate requests.request into a test app call

        method = getattr(self.app, request.method.lower())

        return method(
            url=request.url,
            headers=request.headers,
            params=request.data,
            status=Any.int(),
        )


@step("I send the request to the app")
def sent_request_to_app(context):
    request = context.the_request.request
    response = context.the_app.send_request(request)

    WebTestResponse.register(context, response)
