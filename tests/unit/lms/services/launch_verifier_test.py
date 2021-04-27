import time
from collections import OrderedDict
from unittest.mock import create_autospec, sentinel
from urllib.parse import urlencode

import oauthlib.common
import oauthlib.oauth1
import pytest
from oauthlib.oauth1 import SignatureOnlyEndpoint

from lms.models import ApplicationInstance
from lms.services import ConsumerKeyError, LTIOAuthError
from lms.services.launch_verifier import LaunchVerifier

ONE_HOUR_AGO = str(int(time.time() - 60 * 60))


class TestVerifyLaunchRequest:
    def test_it(self, verify, pyramid_request, ApplicationInstance):
        verify()

        ApplicationInstance.get_by_consumer_key.assert_called_once_with(
            pyramid_request.db, "TEST_OAUTH_CONSUMER_KEY"
        )

    def test_it_raises_if_the_request_is_a_get(self, verify, pyramid_request):
        pyramid_request.method = "GET"

        with pytest.raises(LTIOAuthError):
            verify()

    def test_it_raises_if_the_content_type_is_not_form(self, verify, pyramid_request):
        del pyramid_request.headers["Content-Type"]

        with pytest.raises(LTIOAuthError):
            verify()

    def test_it_raises_if_the_consumer_key_is_not_in_the_db(
        self, verify, ApplicationInstance
    ):
        ApplicationInstance.get_by_consumer_key.return_value = None

        with pytest.raises(ConsumerKeyError):
            verify()

    def test_it_raises_if_the_oauth_signature_is_wrong(self, verify, form_values):
        form_values["oauth_signature"] = "wrong"

        with pytest.raises(LTIOAuthError):
            verify()

    def test_it_raises_if_theres_no_oauth_consumer_key(self, verify, form_values):
        del form_values["oauth_consumer_key"]

        with pytest.raises(LTIOAuthError):
            verify()

    def test_it_doesnt_raise_if_theres_no_oauth_version(self, verify, form_values):
        # This defaults to the correct value if not given.
        del form_values["oauth_version"]
        form_values.sign()

        verify()

    @pytest.mark.parametrize(
        "param", ("oauth_timestamp", "oauth_nonce", "oauth_signature_method")
    )
    def test_it_raises_if_oauth_param_missing(self, verify, form_values, param):
        del form_values[param]
        form_values.sign()

        with pytest.raises(LTIOAuthError):
            verify()

    @pytest.mark.parametrize(
        "param,value",
        (
            ("oauth_timestamp", "ONE_HOUR_AGO"),
            ("oauth_version", "wrong"),
            ("oauth_signature_method", "wrong"),
        ),
    )
    def test_it_raises_if_oauth_param_is_wrong(self, verify, form_values, param, value):
        form_values[param] = value
        form_values.sign()

        with pytest.raises(LTIOAuthError):
            verify()

    # See https://github.com/hypothesis/lms/issues/689
    def test_it_verifies_urls_with_percent_encoded_chars_in_params(
        self, verify, form_values
    ):
        # Add a "url" query parameter where the value, after decoding the query
        # string, contains percent-encoded chars.
        form_values["url"] = "https://en.wikipedia.org/wiki/G%C3%B6reme_National_Park"
        form_values.sign()

        verify()

    @pytest.fixture
    def form_values(self, ApplicationInstance):
        form_values = OrderedDict(
            {
                "oauth_nonce": "11860869681061452641619619597",
                "oauth_timestamp": str(int(time.time())),
                "oauth_version": "1.0",
                "oauth_signature_method": "HMAC-SHA1",
                "oauth_consumer_key": "TEST_OAUTH_CONSUMER_KEY",
            }
        )

        shared_secret = (
            ApplicationInstance.get_by_consumer_key.return_value.shared_secret
        )

        def sign(form_values):
            client = oauthlib.oauth1.Client(
                form_values["oauth_consumer_key"], shared_secret
            )
            form_values["oauth_signature"] = client.get_oauth_signature(
                oauthlib.common.Request(
                    # Note the URL here does not match the `pyramid_request`
                    uri="http://example.com",
                    http_method="POST",
                    body=form_values,
                )
            )

        sign(form_values)
        form_values.sign = lambda: sign(form_values)

        return form_values

    @pytest.fixture
    def verify(self, pyramid_request, form_values):
        verifier = LaunchVerifier(sentinel.context, pyramid_request)

        def verify():
            # Make sure any changes to the form values are reflected in the
            # body before we send it
            pyramid_request.body = urlencode(form_values)

            verifier.verify()

        return verify

    @pytest.fixture(autouse=True)
    def ApplicationInstance(self, patch):
        models = patch("lms.services.launch_verifier.models")
        models.ApplicationInstance.get_by_consumer_key.return_value = create_autospec(
            ApplicationInstance,
            instance=True,
            spec_set=True,
            shared_secret="TEST_SECRET",
        )
        return models.ApplicationInstance


class TestVerifyLaunchRequestMocked:
    def test_it_raises_if_pylti_returns_False(self, verifier, oauth_endpoint):
        oauth_endpoint.validate_request.return_value = False, None

        with pytest.raises(LTIOAuthError):
            verifier.verify()

    def test_it_caches_a_successful_verification_result(self, verifier, oauth_endpoint):
        oauth_endpoint.validate_request.return_value = True, sentinel.request
        # Even if verify_lti_launch_request() is called multiple times, the
        # actual verification is done only once per request.
        verifier.verify()
        verifier.verify()

        assert oauth_endpoint.validate_request.call_count == 1

    def test_it_caches_a_failed_verification_result(self, verifier, oauth_endpoint):
        oauth_endpoint.validate_request.side_effect = ConsumerKeyError()

        # Even if verify_lti_launch_request() is called multiple times, the
        # actual verification is done only once per request.
        with pytest.raises(ConsumerKeyError):
            verifier.verify()
        with pytest.raises(ConsumerKeyError):
            verifier.verify()

        assert oauth_endpoint.validate_request.call_count == 1

    @pytest.fixture
    def oauth_endpoint(self, verifier):
        oauth_endpoint = create_autospec(
            SignatureOnlyEndpoint, instance=True, spec_set=True
        )
        # pylint: disable=protected-access
        verifier._oauth1_endpoint = oauth_endpoint

        return oauth_endpoint

    @pytest.fixture
    def verifier(self, pyramid_request):
        return LaunchVerifier(sentinel.context, pyramid_request)


@pytest.fixture
def pyramid_request(pyramid_request):
    pyramid_request.method = "POST"
    pyramid_request.headers["Content-Type"] = "application/x-www-form-urlencoded"
    pyramid_request.url = "http://example.com?some=noise"

    return pyramid_request
