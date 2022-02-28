import jwt
import uuid
import time

from lms.services import KeyService
from lms.models import Registration


class JWTService:
    def __init__(self, key_service, aes_secret, http, request):
        self._key_service = key_service
        self._aes_secret = aes_secret
        self._http = http
        self._request = request

    def sign(self, registration, message):
        now = int(time.time())

        key = self._key_service.one()
        default_message = {
            "aud": registration.issuer,
            "exp": now + 60 * 60,
            "iat": now - 25,
            "nonce": uuid.uuid4().hex,
            "iss": registration.client_id,
            "sub": registration.client_id,
        }
        message = dict(default_message, **message)

        headers = {"kid": key.kid.hex}

        return jwt.encode(
            message,
            key.private_key(self._aes_secret),
            algorithm="RS256",
            headers=headers,
        )

    # Scopes:
    # 'https://purl.imsglobal.org/spec/lti-ags/scope/lineitem'
    # 'https://purl.imsglobal.org/spec/lti-ags/scope/lineitem.readonly'
    # https://purl.imsglobal.org/spec/lti-nrps/scope/contextmembership.readonly

    def get_access_token(self, registration, scopes):
        # https://datatracker.ietf.org/doc/html/rfc7523
        # https://canvas.instructure.com/doc/api/file.oauth_endpoints.html#post-login-oauth2-token
        jwt = self.sign(
            registration,
            {
                "jti": uuid.uuid4().hex,
                "aud": "https://hypothesis.instructure.com/login/oauth2/token",
            },
        )
        auth_request = {
            "grant_type": "client_credentials",
            "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
            "client_assertion": jwt,
            "scopes": scopes,
        }
        response = self._http.post(
            "https://hypothesis.instructure.com/login/oauth2/token",
            data=auth_request,
        )
        # {
        #    "access_token": "ey",
        #    "token_type": "Bearer",
        #    "expires_in": 3600,
        #    "scope": "https://purl.imsglobal.org/spec/lti-ags/scope/lineitem",
        # }
        return response.json()["access_token"]

    def ltia_request(self, scopes, method, url, headers=None, **kwargs):
        headers = headers or {}

        client_id = self._request.json["aud"]
        issuer = self._request.json["iss"]
        registration = (
            self._request.db.query(Registration)
            .filter_by(issuer=issuer, client_id=client_id)
            .one()
        )

        assert "Authorization" not in headers

        access_token = self.get_access_token(registration, scopes)
        headers["Authorization"] = f"Bearer {access_token}"

        return self._http.request(method, url, headers=headers, **kwargs)


def factory(_context, request):
    return JWTService(
        request.find_service(KeyService),
        request.registry.settings["aes_secret"],
        # From here things might belong to another http service
        request.find_service(name="http"),
        request,
    )
