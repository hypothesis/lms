import re

from behave import step

from tests.bdd.steps.the_url import TheURL


class WebTestResponse:
    def __init__(self, response):
        self.response = response

    def get_body(self):
        return self.response.text

    def get_headers(self):
        return dict(self.response.headers)

    def get_header(self, name):
        return self.response.headers[name]

    def status_code(self):
        return self.response.status_code

    @classmethod
    def register(cls, context, response):
        context.the_response = WebTestResponse(response)


@step("the response header '{header}' matches '{regex}'")
def the_response_header_matches(context, header, regex):
    value = context.the_response.get_header(header)

    assert re.compile(regex).match(value), f'The header matches "{regex}"'


@step("the response status code is {status_code}")
def the_response_status_code_is(context, status_code):
    found_code = context.the_response.status_code()
    if found_code != int(status_code):
        raise AssertionError(
            f"Expected status code '{status_code}' found '{found_code}'"
        )


@step("the response body matches '{regex}'")
def the_response_body_matches(context, regex):
    body = context.the_response.get_body()

    assert re.compile(regex).search(body), f'The body matches "{regex}"'


@step("the response body does not match '{regex}'")
def the_response_body_matches(context, regex):
    body = context.the_response.get_body()

    assert not re.compile(regex).search(body), f'The body does not match "{regex}"'


@step("the response header '{header}' is the URL")
def the_response_header_is_the_url(context, header):
    value = context.the_response.get_header(header)

    TheURL.register(context, value)


@step("I dump the response")
def dump_the_response(context):
    response = context.the_response

    print(f"Dump response: {response.status_code()}")
    print(response.get_headers())
    print(response.get_body())
