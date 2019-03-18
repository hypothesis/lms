import time
from unittest import mock

import oauthlib.oauth1
import oauthlib.common
import pytest
from pylti.common import LTIException

from lms.services.launch_verifier import LaunchVerifier
from lms.services import NoConsumerKey
from lms.services import ConsumerKeyError
from lms.services import LTIOAuthError


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

    def test_it_gets_the_shared_secret_from_the_db(self, ai_getter, launch_verifier):
        launch_verifier.verify()

        ai_getter.shared_secret.assert_called_once_with("TEST_OAUTH_CONSUMER_KEY")

    def test_it_raises_if_the_consumer_key_isnt_in_the_db(
        self, launch_verifier, ai_getter
    ):
        ai_getter.shared_secret.side_effect = ConsumerKeyError()

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

    @pytest.fixture
    def launch_verifier(self, pyramid_request):
        return LaunchVerifier(mock.sentinel.context, pyramid_request)

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.url = "http://example.com/"

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
