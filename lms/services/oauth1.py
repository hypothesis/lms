from requests_oauthlib import OAuth1


class OAuth1Service:
    """Provides OAuth1 convenience functions."""

    def __init__(self, _context, request):
        self.request = request
        self.ai_getter_service = request.find_service(name="ai_getter")

    def get_client(self):
        """
        Get an OAUth1 client that can be used to sign HTTP requests.

        To sign a request with the client pass it as the `auth` parameter to
        `requests.post()`.

        :rtype: OAuth1
        """

        consumer_key = self.request.lti_user.oauth_consumer_key
        shared_secret = self.ai_getter_service.shared_secret(consumer_key)

        return OAuth1(
            client_key=consumer_key,
            client_secret=shared_secret,
            signature_method="HMAC-SHA1",
            signature_type="auth_header",
            # Include the body when signing the request, this defaults to
            # `False` for non-form encoded bodies.
            force_include_body=True,
        )
