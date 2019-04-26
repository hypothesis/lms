import jwt
from jwt.exceptions import InvalidTokenError
from pyramid.settings import asbool, aslist

from ._exceptions import SettingError


__all__ = ["FeatureFlagsCookieHelper", "JWTCookieHelper"]


class FeatureFlagsCookieHelper:
    """Helper for getting and setting feature flags cookies."""

    def __init__(self, request):
        # The set of feature flags that are allowed to be toggled on or off by the
        # feature flags cookie.
        self._allowed_flags = aslist(
            request.registry.settings.get("feature_flags_allowed_in_cookie", "") or ""
        )
        self._jwt_cookie_helper = JWTCookieHelper("feature_flags", request)
        self._request = request

    def set_cookie(self, response):
        flags = self._parse_flags(self._request.params)
        self._jwt_cookie_helper.set(response, flags)

    def get(self, flag):
        return self.get_all().get(flag, False)

    def get_all(self):
        return self._parse_flags(self._jwt_cookie_helper.get())

    def _parse_flags(self, flags):
        return {flag: asbool(flags.get(flag, False)) for flag in self._allowed_flags}


class JWTCookieHelper:
    """Helper for getting and setting a JWT-encoded cookie."""

    def __init__(self, name, request):
        # The secret used to sign the cookie.
        try:
            self._secret = request.registry.settings["feature_flags_cookie_secret"]
        except KeyError:
            raise SettingError(
                "The feature_flags_cookie_secret deployment setting is required"
            )

        self._name = name
        self._request = request

    def set(self, response, payload):
        jwt_bytes = jwt.encode(payload, self._secret, algorithm="HS256")
        response.set_cookie(
            self._name,
            jwt_bytes,
            max_age=31536000,  # One year in seconds.
            overwrite=True,
            secure=not self._request.registry.settings.get("debug", False),
        )

    def get(self):
        jwt_bytes = self._request.cookies.get(self._name, "")
        try:
            return jwt.decode(jwt_bytes, self._secret, algorithms=["HS256"])
        except InvalidTokenError:
            return {}
