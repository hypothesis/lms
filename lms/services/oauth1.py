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
        application_instance = self._application_instance_service.get_current()

        return OAuth1(
            client_key=application_instance.consumer_key,
            client_secret=application_instance.shared_secret,
            signature_method="HMAC-SHA1",
            signature_type="auth_header",
            # Include the body when signing the request, this defaults to
            # `False` for non-form encoded bodies.
            force_include_body=True,
        )
