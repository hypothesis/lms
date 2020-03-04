"""Form and manipulate HTTP requests."""

from behave import given  # pylint:disable=no-name-in-module
from requests import Request

from tests.bdd.step_context import StepContext


class TheRequest(StepContext):
    context_key = "the_request"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.request = None

    def new_request(self, method, url):
        self.request = Request(method, url)

    def set_header(self, header, value):
        self.request.headers[header] = value

    def get_url(self):
        return self.request.url

    def get_method(self):
        return self.request.method

    def set_form_parameters(self, params):
        self.request.data = params

    def do_teardown(self):
        self.request = None


@given("I start a '{method}' request to '{url}'")
def start_request(context, method, url):
    context.the_request.new_request(method, url)


@given("I set the request header '{header}' to '{value}'")
def set_header(context, header, value):
    context.the_request.set_header(header, value)


@given("I set the form parameters from the fixture '{fixture_name}'")
def set_form_parameters_from_fixture(context, fixture_name):
    context.the_request.set_form_parameters(
        context.the_fixture.get_fixture(fixture_name)
    )
