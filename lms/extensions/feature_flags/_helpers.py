import jwt
from jwt.exceptions import InvalidTokenError
from pyramid.settings import asbool, aslist

from ._exceptions import SettingError


def as_tristate(value):
    """
    Coerce the given value to True, False or None.

    Like Pyramid's `asbool` this will attempt to interpret the value given to
    it as either True or False, but in addition allows for None types.

    The following items are considered as None:

     * Empty string
     * None
     * "None" or "none"

    All other values are handle as per `asbool`.
    """
    if value in {None, True, False}:
        return value

    if isinstance(value, str) and value.lower() in {"", "none"}:
        return None

    return asbool(value)


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
        return self.get_all().get(flag, None)

    def get_all(self):
        return self._parse_flags(self._jwt_cookie_helper.get())

    def _parse_flags(self, flags):
        return {flag: as_tristate(flags.get(flag)) for flag in self._allowed_flags}


class JWTCookieHelper:
    """Helper for getting and setting a JWT-encoded cookie."""

    def __init__(self, name, request):
        # The secret used to sign the cookie.
        try:
            self._secret = request.registry.settings["feature_flags_cookie_secret"]
        except KeyError as err:
            raise SettingError(
                "The feature_flags_cookie_secret deployment setting is required"
            ) from err

        self._name = name
        self._request = request

    def set(self, response, payload):
        jwt_bytes = jwt.encode(payload, self._secret, algorithm="HS256")
        response.set_cookie(
            self._name,
            jwt_bytes,
            max_age=31536000,  # One year in seconds.
            overwrite=True,
            # We want this cookie to be sent when the LMS app is loaded inside
            # an iframe, and thus in a third-party context, from within the LMS.
            samesite="None",
            # Setting `SameSite="None"` requires that we also set the `Secure`
            # flag per https://tools.ietf.org/html/draft-west-cookie-incrementalism-00#section-3.2.
            secure=True,
        )

    def get(self):
        jwt_bytes = self._request.cookies.get(self._name, "")

        if not jwt_bytes:
            return {}

        try:
            return jwt.decode(jwt_bytes, self._secret, algorithms=["HS256"])
        except InvalidTokenError:
            return {}
