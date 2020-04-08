import time
from unittest import mock
from urllib.parse import urlencode

import oauthlib.common
import oauthlib.oauth1
import pytest
from pylti.common import LTIException

from lms.services import ConsumerKeyError, LTIOAuthError, NoConsumerKey
from lms.services.launch_verifier import LaunchVerifier

ONE_HOUR_AGO = str(int(time.time() - 60 * 60))


class TestVerifyLaunchRequest:
    def test_it_doesnt_raise_if_the_request_is_valid(self, launch_verifier):
        launch_verifier.verify()

    def test_it_raises_if_theres_no_oauth_consumer_key(
        self, launch_verifier, pyramid_request
    ):
        del pyramid_request.params["oauth_consumer_key"]

        with pytest.raises(NoConsumerKey):
            launch_verifier.verify()

    def test_it_gets_the_shared_secret_from_the_db(
        self, launch_verifier, pyramid_request, models
    ):
        launch_verifier.verify()

        models.ApplicationInstance.get.assert_called_once_with(
            pyramid_request.db, "TEST_OAUTH_CONSUMER_KEY"
        )

    def test_it_raises_if_the_consumer_key_isnt_in_the_db(
        self, launch_verifier, models
    ):
        models.ApplicationInstance.get.return_value = None

        with pytest.raises(ConsumerKeyError):
            launch_verifier.verify()

    def test_it_raises_if_the_oauth_signature_is_wrong(
        self, launch_verifier, pyramid_request
    ):
        pyramid_request.params["oauth_signature"] = "wrong"

        with pytest.raises(LTIOAuthError):
            launch_verifier.verify()

    def test_it_raises_if_the_oauth_timestamp_has_expired(
        self, launch_verifier, pyramid_request
    ):
        pyramid_request.params["oauth_timestamp"] = ONE_HOUR_AGO
        sign(pyramid_request)

        with pytest.raises(LTIOAuthError):
            launch_verifier.verify()

    def test_it_raises_if_theres_no_oauth_timestamp(
        self, launch_verifier, pyramid_request
    ):
        del pyramid_request.params["oauth_timestamp"]
        sign(pyramid_request)

        with pytest.raises(LTIOAuthError):
            launch_verifier.verify()

    def test_it_raises_if_theres_no_oauth_nonce(self, launch_verifier, pyramid_request):
        del pyramid_request.params["oauth_nonce"]
        sign(pyramid_request)

        with pytest.raises(LTIOAuthError):
            launch_verifier.verify()

    def test_it_raises_if_oauth_version_is_wrong(
        self, launch_verifier, pyramid_request
    ):
        pyramid_request.params["oauth_version"] = "wrong"
        sign(pyramid_request)

        with pytest.raises(LTIOAuthError):
            launch_verifier.verify()

    def test_it_doesnt_raise_if_theres_no_oauth_version(
        self, launch_verifier, pyramid_request
    ):
        # oauth_version defaults to the correct value if not given.
        del pyramid_request.params["oauth_version"]
        sign(pyramid_request)

        launch_verifier.verify()

    def test_it_raises_if_oauth_signature_method_is_wrong(
        self, launch_verifier, pyramid_request
    ):
        pyramid_request.params["oauth_signature_method"] = "wrong"
        sign(pyramid_request)

        with pytest.raises(LTIOAuthError):
            launch_verifier.verify()

    def test_it_raises_if_theres_no_oauth_signature_method(
        self, launch_verifier, pyramid_request
    ):
        del pyramid_request.params["oauth_signature_method"]
        sign(pyramid_request)

        with pytest.raises(LTIOAuthError):
            launch_verifier.verify()

    def test_it_raises_if_pylti_returns_False(self, launch_verifier, pylti):
        pylti.common.verify_request_common.return_value = False

        with pytest.raises(LTIOAuthError):
            launch_verifier.verify()

    def test_it_caches_a_successful_verification_result(self, launch_verifier, pylti):
        # Even if verify_lti_launch_request() is called multiple times, the
        # actual verification is done only once per request.
        launch_verifier.verify()
        launch_verifier.verify()
        launch_verifier.verify()

        assert pylti.common.verify_request_common.call_count == 1

    def test_it_caches_a_failed_verification_result(self, launch_verifier, pylti):
        pylti.common.verify_request_common.side_effect = LTIException()

        # Even if verify_lti_launch_request() is called multiple times, the
        # actual verification is done only once per request.
        with pytest.raises(LTIOAuthError):
            launch_verifier.verify()
        with pytest.raises(LTIOAuthError):
            launch_verifier.verify()
        with pytest.raises(LTIOAuthError):
            launch_verifier.verify()

        assert pylti.common.verify_request_common.call_count == 1

    # See https://github.com/hypothesis/lms/issues/689
    def test_it_verifies_urls_with_percent_encoded_chars_in_params(
        self, pyramid_request
    ):
        # Add a "url" query parameter where the value, after decoding the query
        # string, contains percent-encoded chars.
        params = {"url": "https://en.wikipedia.org/wiki/G%C3%B6reme_National_Park"}
        pyramid_request.POST.update(params)

        # Sign the pyramid_request using oauthlib.
        sign(pyramid_request)

        # Update `pyramid_request.url` to include the query string.
        # We do this after signing because oauthlib will, correctly,
        # include both the "url" param from `pyramid_request.params` and the "url"
        # param from the query string. PyLTI however will only retain one copy
        # when generating the signature for verification.
        pyramid_request.url += "?" + urlencode(params)

        launch_verifier = LaunchVerifier(mock.sentinel.context, pyramid_request)
        launch_verifier.verify()

    @pytest.fixture
    def launch_verifier(self, pyramid_request):
        return LaunchVerifier(mock.sentinel.context, pyramid_request)

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        # `pyramid.testing.DummyRequest` sets `url` and `path_url` attrs without
        # a path by default. oauthlib however normalizes the URL to include a
        # path when it generates the signature base string, whereas PyLTI does
        # not. Add an empty path to both to match a real application.
        pyramid_request.url += "/"
        pyramid_request.path_url += "/"

        # Add the OAuth 1 params (version, nonce, timestamp, ...)
        oauthlib_client = oauthlib.oauth1.Client(
            pyramid_request.params["oauth_consumer_key"]
        )
        oauthlib_request = oauthlib.common.Request(
            pyramid_request.url, pyramid_request.method
        )
        pyramid_request.params = dict(
            oauthlib_client.get_oauth_params(oauthlib_request)
        )

        sign(pyramid_request)

        return pyramid_request

    @pytest.fixture
    def pylti(self, patch):
        pylti = patch("lms.services.launch_verifier.pylti")
        pylti.common.LTIException = LTIException
        return pylti


def sign(pyramid_request):
    """Add or replace pyramid_request's OAuth 1 signature param."""
    oauthlib_client = oauthlib.oauth1.Client(
        pyramid_request.params["oauth_consumer_key"], "TEST_SECRET"
    )
    oauthlib_request = oauthlib.common.Request(
        pyramid_request.url, pyramid_request.method, body=pyramid_request.params
    )
    pyramid_request.params["oauth_signature"] = oauthlib_client.get_oauth_signature(
        oauthlib_request
    )


@pytest.fixture(autouse=True)
def models(patch):
    models = patch("lms.services.launch_verifier.models")
    models.ApplicationInstance.get.return_value = mock.Mock(shared_secret="TEST_SECRET")
    return models
