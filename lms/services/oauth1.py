import base64
import hashlib
import hmac
import uuid
from datetime import datetime
from urllib import parse

from oauthlib.oauth1.rfc5849 import signature
from requests_oauthlib import OAuth1

from lms.models import ApplicationInstance


class OAuth1Service:
    """Provides OAuth1 convenience functions."""

    def get_client(self, application_instance: ApplicationInstance) -> OAuth1:
        """
        Get an OAUth1 client that can be used to sign HTTP requests for `application_instance`.

        To sign a request with the client pass it as the `auth` parameter to
        `requests.post()`.
        """
        return OAuth1(
            client_key=application_instance.consumer_key,
            client_secret=application_instance.shared_secret,
            signature_method="HMAC-SHA1",
            signature_type="auth_header",
            # Include the body when signing the request, this defaults to
            # `False` for non-form encoded bodies.
            force_include_body=True,
        )

    def sign(self, application_instance, url: str, method: str, data: dict) -> dict:
        """
        Sign data following the oauth1 spec.

        Useful when not using these values for a HTTP requests with the client from get_client.
        """
        client_key = application_instance.consumer_key
        # Secret and token need to joined by "&".
        # We don't have a token but the trailing `&` is required
        client_secret = application_instance.shared_secret + "&"

        parsed_url = parse.urlparse(url)

        # Oauth values
        payload = {
            "oauth_version": "1.0",
            "oauth_nonce": uuid.uuid4().hex,
            "oauth_timestamp": str(round(datetime.now().timestamp())),  # noqa: DTZ005
            "oauth_consumer_key": client_key,
            "oauth_signature_method": "HMAC-SHA1",
        }
        # Include the data we want to send in the payload
        payload.update(data)

        # Clean parameters and generate the plain text to sign
        params = signature.collect_parameters(
            uri_query=parsed_url.query,
            body=payload,
            exclude_oauth_signature=False,
            with_realm=False,
        )
        normalized_parameters = signature.normalize_parameters(params)
        normalized_uri = signature.base_string_uri(url, parsed_url.netloc)
        base_string = signature.signature_base_string(
            method, normalized_uri, normalized_parameters
        )

        # Generate the digest
        hashed = hmac.new(
            client_secret.encode("utf-8"), base_string.encode("utf-8"), hashlib.sha1
        )
        digest = base64.b64encode(hashed.digest()).decode("utf-8")

        payload["oauth_signature"] = digest
        return payload


def factory(_context, _request):
    return OAuth1Service()
