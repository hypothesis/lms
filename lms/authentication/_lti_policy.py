from pyramid import security

from lms.authentication import _helpers


class LTIAuthenticationPolicy:
    def authenticated_userid(self, request):
        return self.unauthenticated_userid(request)

    def unauthenticated_userid(self, request):  # pylint:disable=no-self-use
        if request.lti_user is None:
            return None

        return _helpers.authenticated_userid(request.lti_user)

    def effective_principals(self, request):
        userid = self.authenticated_userid(request)
        principals = [security.Everyone]

        if userid:
            principals.extend([security.Authenticated, userid])

        return principals

    def remember(self, request, userid, **kw):
        pass

    def forget(self, request):
        pass
