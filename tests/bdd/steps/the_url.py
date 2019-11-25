"""Create, manipulate and make assertions about URLs."""

import re
from urllib.parse import parse_qs, urlparse

from behave import then

from tests.bdd.step_context import StepContext


class TheURL(StepContext):
    context_key = "the_url"
    singleton = False

    def __init__(self, url, **kwargs):
        self.raw_url = url
        self.url = urlparse(url)
        self.query = parse_qs(self.url.query)

    def bare_url(self):
        return self.url._replace(query=None).geturl()


@then("the url matches '{bare_url}'")
def the_url_matches(context, bare_url):
    found_url = context.the_url.bare_url()

    if found_url != bare_url:
        raise AssertionError(f"Expected url '{bare_url}' found '{found_url}'")


@then("the url matches the value")
def the_url_matches_the_value(context):
    the_url_matches(context, context.the_value)


@then("the url query parameter '{param}' matches '{regex}'")
def the_url_query_parameter_matches(context, param, regex):
    value = context.the_url.query.get(param)
    value = value[0]

    if not re.compile(regex).match(value):
        raise AssertionError(
            f"Expected param '{param}' to match regex '{regex}', but found: '{value}'"
        )
