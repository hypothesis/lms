from urllib.parse import urlencode

from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config
from lms.models import Registration

from lms.services import KeyService


@view_config(
    route_name="lti_oidc",
    request_method=("POST", "GET"),  ## BB get, canvas POST
    renderer="json",
)
def lti_oidc(request):
    # http://www.imsglobal.org/spec/security/v1p0/#step-2-authentication-request

    # TODO error handling
    # TODO registration service
    registration = (
        request.db.query(Registration)
        .filter_by(issuer=request.params["iss"], client_id=request.params["client_id"])
        .one()
    )  # As far as I can tell there could be multiple deployments for this. We don't have the deployment_id at this moment but we only care about
    # - Do we have registered this client_id
    # - Getting the auth_url for the issuer (issuer could be it's own table then)

    params = {
        "scope": "openid",
        "response_type": "id_token",
        "response_mode": "form_post",
        "prompt": "none",
        "client_id": request.params["client_id"],
        "redirect_uri": request.params["target_link_uri"],
        "state": "STATE",  # TODO
        "nonce": "NONCE",  # TODO
        "login_hint": request.params["login_hint"],
        "lti_message_hint": request.params["lti_message_hint"],
    }

    return HTTPFound(location=f"{registration.auth_login_url}?{urlencode(params)}")


@view_config(
    route_name="jwts",
    request_method="GET",
    renderer="json",
)
def jwts(request):
    key_service = request.find_service(KeyService)
    keys = key_service.all()

    return {"keys": [k.jwk for k in keys]}
