from pyramid.view import view_config

from lms.security import Permissions
from lms.services import GrantTokenService


@view_config(permission=Permissions.API, renderer="json", route_name="api.grant_token")
def grant_token(request):
    """
    Return a grant token that the Hypothesis client can use to log in to H.

    See https://h.readthedocs.io/en/latest/publishers/authorization-grant-tokens/.
    """

    grant_token_svc = request.find_service(GrantTokenService)
    h_user = request.lti_user.h_user

    return {"grant_token": grant_token_svc.generate_token(h_user)}
