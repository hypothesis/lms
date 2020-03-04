"""Deal with OAuth 1 signing."""

import time

import oauthlib
from behave import step  # pylint:disable=no-name-in-module

from tests.bdd.step_context import StepContext


class OAuth1Context(StepContext):
    context_key = "oath_context"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.consumer_key = None
        self.shared_secret = None
        self.client = None

    def set_shared_secret(self, shared_secret):
        self.shared_secret = shared_secret

        self._make_client()

    def set_consumer_key(self, consumer_key):
        self.consumer_key = consumer_key

        self._make_client()

    def _make_client(self):
        if self.shared_secret is None or self.consumer_key is None:
            return

        self.client = oauthlib.oauth1.Client(self.consumer_key, self.shared_secret)

    def _make_nonce(self):
        return "38d6db30e395417659d068164ca95169"

    def sign_params(self, url, method, params):
        if not self.client:
            raise ValueError("You must set the consumer key and nonce first")

        params.update(
            {
                "oauth_consumer_key": self.consumer_key,
                "oauth_nonce": self._make_nonce(),
                "oauth_timestamp": str(int(time.time())),
            }
        )
        params["oauth_signature"] = self.client.get_oauth_signature(
            oauthlib.common.Request(url, method, body=params)
        )

    def do_teardown(self):
        self.context_key = None
        self.shared_secret = None
        self.client = None


@step("the OAuth 1 consumer key is '{consumer_key}'")
def set_oauth_consumer_key(context, consumer_key):
    context.oath_context.set_consumer_key(consumer_key)


@step("the OAuth 1 shared secret is '{shared_secret}'")
def set_oauth_shared_secret(context, shared_secret):
    context.oath_context.set_shared_secret(shared_secret)


@step("I OAuth 1 sign the fixture '{fixture_name}'")
def oauth_sign_params(context, fixture_name):
    context.oath_context.sign_params(
        url=context.the_request.get_url(),
        method=context.the_request.get_method(),
        params=context.the_fixture.get_fixture(fixture_name),
    )
