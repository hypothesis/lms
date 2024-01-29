import base64
import hashlib
import hmac
import uuid
from datetime import datetime
from urllib import parse

from requests import Request
from requests_oauthlib import OAuth1


class OAuth1Service:
    """Provides OAuth1 convenience functions."""

    def __init__(self, _context, request):
        self._request = request

    def get_client(self, signature_type="auth_header"):
        """
        Get an OAUth1 client that can be used to sign HTTP requests.

        To sign a request with the client pass it as the `auth` parameter to
        `requests.post()`.

        :rtype: OAuth1
        """
        application_instance = self._request.lti_user.application_instance

        return OAuth1(
            client_key=application_instance.consumer_key,
            client_secret=application_instance.shared_secret + "&",
            signature_method="HMAC-SHA1",
            signature_type=signature_type,
            # Include the body when signing the request, this defaults to
            # `False` for non-form encoded bodies.
            force_include_body=True,
        )

    def sign(self, url, method, data):
        application_instance = self._request.lti_user.application_instance

        client_key = application_instance.consumer_key
        client_secret = application_instance.shared_secret + "&"

        # Oauth values
        payload = {
            "oauth_version": "1.0",
            "oauth_nonce": uuid.uuid4().hex,
            "oauth_timestamp": round(datetime.now().timestamp()),
            "oauth_consumer_key": client_key,
            "oauth_signature_method": "HMAC-SHA1",
        }
        # Include the data we want to send in the payload
        payload.update(data)

        signature_parts = [
            method.upper(),
            # We need to encode `/`, don't include it in "safe"
            parse.quote(url, safe=""),
            # These need to be sorted before generating a string
            parse.quote_plus(
                parse.urlencode(sorted(payload.items()), quote_via=parse.quote)
            ),
        ]
        raw_text = "&".join(signature_parts)

        # Generate the digest
        hashed = hmac.new(
            client_secret.encode("utf-8"), raw_text.encode("utf-8"), hashlib.sha1
        )
        digest = base64.b64encode(hashed.digest()).decode("utf-8")

        # And append it to the payload
        payload["oauth_signature"] = digest

        return payload

    def get_auth_parameters(
        self, url: str, data: dict, method: str = "POST"
    ) -> dict[str, str]:
        request = Request(
            method,
            url=url,
            headers=data,
            auth=self.get_client(signature_type="body"),
        )
        raw_params = request.prepare().body

        return {
            key.decode(): value[0].decode()
            for key, value in parse.parse_qs(raw_params).items()
        }
