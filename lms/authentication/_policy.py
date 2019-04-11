import functools

from pyramid.authentication import AuthTktAuthenticationPolicy

from lms.authentication._lti_policy import LTIAuthenticationPolicy
from lms.security import groupfinder


__all__ = ("AuthenticationPolicy",)


class AuthenticationPolicy:
    """Top-level authentication policy that delegates to sub-policies."""

    def __init__(self, lms_secret):
        self._lti_authentication_policy = LTIAuthenticationPolicy()
        self._auth_tkt_authentication_policy = AuthTktAuthenticationPolicy(
            lms_secret, callback=groupfinder, hashalg="sha512"
        )

    def authenticated_userid(self, request):
        return self._policy(request).authenticated_userid(request)

    def unauthenticated_userid(self, request):
        return self._policy(request).unauthenticated_userid(request)

    def effective_principals(self, request):
        return self._policy(request).effective_principals(request)

    def remember(self, request, userid, **kw):
        return self._policy(request).remember(request, userid, **kw)

    def forget(self, request):
        return self._policy(request).forget(request)

    @functools.lru_cache(maxsize=1)
    def _policy(self, request):
        if self._lti_authentication_policy.authenticated_userid(request):
            return self._lti_authentication_policy

        return self._auth_tkt_authentication_policy
