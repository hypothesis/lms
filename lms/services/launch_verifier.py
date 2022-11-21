"""LTI launch request verifier service."""
from oauthlib.oauth1 import RequestValidator, SignatureOnlyEndpoint

from lms.services.application_instance import ApplicationInstanceNotFound


class LTILaunchVerificationError(Exception):
    """
    Raised when LTI launch request verification fails.

    This is the base class for all LTI launch request verification errors.
    Different subclasses of this exception class are raised for specific
    failure types.
    """


class LTIOAuthError(LTILaunchVerificationError):
    """Raised when OAuth signature verification of a launch request fails."""


class LaunchVerifier:
    """LTI launch request verifier."""

    def __init__(self, _context, request):
        self._request = request

        self._request_verified = False
        self._exception = None

    def verify(self, secret):
        """
        Raise if the current request isn't a valid LTI launch request.

        :raise LTILaunchVerificationError: if the request isn't a valid LTI
          launch request. Different :exc:`LTILaunchVerificationError`
          subclasses are raised for different types of verification failure.

        :raise NoConsumerKey: If the request has no oauth_consumer_key
          parameter (maybe it's not an LTI launch request at all?)

        :raise LTIOAuthError: If OAuth 1.0 verification of the request and its
          signature fails
        """
        if not self._request_verified:
            try:
                self._verify(secret)
            except LTILaunchVerificationError as err:
                self._exception = err
            finally:
                self._request_verified = True

        if self._exception:
            raise self._exception

    def _verify(self, secret):
        # As part of our parsing, LTI11AuthSchema has been applied to
        # the request before we get this far. This means that all of the
        # results are in `params` but they might have come from either the body
        # or GET params. `oauthlib` cares a great deal about where things
        # should come from, so we need to put them back in the right place.

        method = self._request.method
        if method != "POST":
            raise LTIOAuthError("LTI launches should use POST")

        oauth1_endpoint = self._oauth1_endpoint = SignatureOnlyEndpoint(
            _OAuthRequestValidator(secret=secret)
        )

        is_valid, _request = oauth1_endpoint.validate_request(
            # The docs for `validate_request` say to send the full URL with
            # params, but here we don't. I think LTI tool consumers sign
            # without any params, but some times add some (looking at you
            # Canvas)
            uri=self._request.path_url,
            http_method=method,
            body=self._request.body,
            headers=self._request.headers,
        )

        if not is_valid:
            raise LTIOAuthError("OAuth signature is not valid")


class _OAuthRequestValidator(RequestValidator):
    # Value lifted from `oauth2` which is an `oauth1` library as was used by
    # PyLTI. The default in `oauthlib` is 600
    timestamp_lifetime = 300  # In seconds, five minutes.

    # Tell oauthlib we are chill about http for local testing
    enforce_ssl = False

    def __init__(self, secret):
        super().__init__()

        self._secret = secret

    def check_client_key(self, client_key):
        """Check that the client key only contains safe characters."""

        return True

    def check_nonce(self, nonce):
        """Check that the nonce only contains only safe characters."""

        return True

    def validate_timestamp_and_nonce(
        # pylint: disable=too-many-arguments
        # Not our design, we have to fit in with this API
        self,
        client_key,
        timestamp,
        nonce,
        request,
        request_token=None,
        access_token=None,
    ):
        """Validate that the nonce has not been used before."""

        return True

    def validate_client_key(self, client_key, request):
        """Validate that supplied client key is registered and valid."""

        # This is slightly incorrect, but we are just going to say the client
        # key is fine! Even though this might not be true. This is because
        # we would have to look up the DB to find out, and we _have_ to do
        # that in the next step `get_client_secret()`
        return True

    def get_client_secret(self, client_key, request):
        """Retrieve the client secret associated with the client key."""
        return self._secret
