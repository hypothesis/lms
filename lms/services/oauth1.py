from requests_oauthlib import OAuth1


class OAuth1Service:
    """Provides OAuth1 convenience functions."""

    def __init__(self, _context, request):
        self._request = request
        self._application_instance_service = request.find_service(
            name="application_instance"
        )

    def get_client(self):
        """
        Get an OAUth1 client that can be used to sign HTTP requests.

        To sign a request with the client pass it as the `auth` parameter to
        `requests.post()`.

        :rtype: OAuth1
        """

        ai = self._request.lti_user.application_instance
        consumer_key = ai.consumer_key
        shared_secret = ai.shared_secret

        return OAuth1(
            client_key=consumer_key,
            client_secret=shared_secret,
            signature_method="HMAC-SHA1",
            signature_type="auth_header",
            # Include the body when signing the request, this defaults to
            # `False` for non-form encoded bodies.
            force_include_body=True,
        )
