from pyramid.view import view_config

from lms.services import RSAKeyService


@view_config(route_name="lti.jwks", request_method="GET", renderer="json")
def jwks(request):
    """Expose RSA public keys for LMSs to verify our LTI Advantage API calls."""
    return {"keys": request.find_service(RSAKeyService).get_all_public_jwks()}
