"""
LTI service.

This is a place to put LTI-related methods where they can be called from
anywhere in the code, they can have access to the request and context, and they
can have state (e.g. to cache the results of computations).
"""
import pylti.common

from lms.services import NoConsumerKey
from lms.services import ConsumerKeyError
from lms.services import LTIOAuthError


class LTIService:
    """A collection of LTI-related methods."""

    def __init__(self, _context, request):
        self._request = request

    def verify_launch_request(self):
        """
        Raise if the current request isn't a valid LTI launch request.

        :raise ~lms.services.LTILaunchVerificationError: if the request isn't a
          valid LTI launch request. Different
          :exc:`~lms.services.LTILaunchVerificationError` subclasses are raised
          for different types of verification failure.

        :raise NoConsumerKey: If the request has no ``oauth_consumer_key``
          parameter (maybe it's not an LTI launch request at all?)

        :raise ConsumerKeyError: If the request's ``oauth_consumer_key``
          parameter isn't found in our database (this appears to be an invalid
          LTI launch request).

        :raise LTIOAuthError: If OAuth 1.0 verification of the request and its
          signature fails
        """
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
                self._request.url,
                self._request.method,
                dict(self._request.headers),
                dict(self._request.params),
            )
        except pylti.common.LTIException:
            raise LTIOAuthError()
        except KeyError:
            # pylti crashes if certain params (e.g. oauth_nonce) are missing
            # from the request.
            raise LTIOAuthError()

        if not valid:
            raise LTIOAuthError()
