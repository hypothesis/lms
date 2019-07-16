"""LTI launch request verifier service."""
import pylti.common

from lms.services import LTILaunchVerificationError
from lms.services import NoConsumerKey
from lms.services import ConsumerKeyError
from lms.services import LTIOAuthError


__all__ = ["LaunchVerifier"]


class LaunchVerifier:
    """LTI launch request verifier."""

    def __init__(self, _context, request):
        self._request = request
        self._request_verified = False
        self._exception = None

    def verify(self):
        """
        Raise if the current request isn't a valid LTI launch request.

        :raise LTILaunchVerificationError: if the request isn't a valid LTI
          launch request. Different :exc:`LTILaunchVerificationError`
          subclasses are raised for different types of verification failure.

        :raise NoConsumerKey: If the request has no ``oauth_consumer_key``
          parameter (maybe it's not an LTI launch request at all?)

        :raise ConsumerKeyError: If the request's ``oauth_consumer_key``
          parameter isn't found in our database (this appears to be an invalid
          LTI launch request).

        :raise LTIOAuthError: If OAuth 1.0 verification of the request and its
          signature fails
        """
        if not self._request_verified:
            try:
                self._verify()
            except LTILaunchVerificationError as err:
                self._exception = err
            finally:
                self._request_verified = True

        if self._exception:
            raise self._exception  # pylint: disable=raising-bad-type

    def _verify(self):
        try:
            consumer_key = self._request.params["oauth_consumer_key"]
        except KeyError:
            raise NoConsumerKey()

        try:
            shared_secret = self._request.find_service(name="ai_getter").shared_secret(
                consumer_key
            )
        except ConsumerKeyError:  # pylint: disable=try-except-raise
            raise

        consumers = {}
        consumers[consumer_key] = {"secret": shared_secret}

        try:
            valid = pylti.common.verify_request_common(
                consumers,
                # We pass only the host + path of the URL (`request.path_url`)
                # to `verify_request_common` in the `url` arg because:
                #
                # - Query params are also passed in `request.params` below
                # - If query params are passed in both the URL and the `parameters`
                #   dict, then the value from the URL is used
                # - If values in the query param contain percent-encoded characters,
                #   these are incorrectly _decoded_ in the result, whereas they
                #   are handled correctly if passed in the `parameters` arg.
                self._request.path_url,
                self._request.method,
                dict(self._request.headers),
                dict(self._request.params),
            )
        except pylti.common.LTIException as err:
            raise LTIOAuthError() from err
        except KeyError:
            # pylti crashes if certain params (e.g. oauth_nonce) are missing
            # from the request.
            raise LTIOAuthError()

        if not valid:
            raise LTIOAuthError()
