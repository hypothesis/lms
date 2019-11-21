import time

import oauthlib
from behave import step


class OAuth1Context:
    def __init__(self):
        self.consumer_key = None
        self.nonce = None
        self.client = None

    def set_nonce(self, nonce):
        self.nonce = nonce

        self._make_client()

    def set_consumer_key(self, consumer_key):
        self.consumer_key = consumer_key

        self._make_client()

    def _make_client(self):
        if self.nonce is None or self.consumer_key is None:
            return

        self.client = oauthlib.oauth1.Client(self.consumer_key, self.nonce)

    def sign_params(self, url, method, params):
        if not self.client:
            raise ValueError('You must set the consumer key and nonce first')

        params.update(
            {
                "oauth_consumer_key": self.consumer_key,
                "oauth_nonce": self.nonce,
                "oauth_timestamp": str(int(time.time())),
            }
        )
        params["oauth_signature"] = self.client.get_oauth_signature(
            oauthlib.common.Request(f"http://localhost{url}", method, body=params)
        )

    @classmethod
    def register(cls, context):
        context.oath_context = OAuth1Context()


@step("the OAuth 1 consumer key is '{consumer_key}'")
def set_oauth_consumer_key(context, consumer_key):
    context.oath_context.set_consumer_key(consumer_key)


@step("the OAuth 1 nonce is '{nonce}'")
def set_oauth_nonce(context, nonce):
    context.oath_context.set_nonce(nonce)


@step("I OAuth 1 sign the fixture '{fixture_name}'")
def oauth_sign_params(context, fixture_name):
    context.oath_context.sign_params(
        url=context.the_request.get_url(),
        method=context.the_request.get_method(),
        params=context.the_fixture.get_fixture(fixture_name)
    )
