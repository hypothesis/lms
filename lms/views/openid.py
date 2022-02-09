from pyramid.httpexceptions import HTTPFound

from pyramid.view import view_config
from urllib.parse import urlencode


@view_config(
    route_name="lti_oidc",
    request_method="POST",
    renderer="json",
)
def lti_oidc(request):
    launch_url = request.route_url("lti_launches")

    # http://www.imsglobal.org/spec/security/v1p0/#step-2-authentication-request
    params = {
        "scope": "openid",
        "response_type": "id_token",
        "response_mode": "form_post",
        "prompt": "none",
        "client_id": request.params["client_id"],
        "redirect_uri": launch_url,
        "state": "STATE",  # TODO
        "nonce": "NONCE",  # TODO
        "login_hint": request.params["login_hint"],
        "lti_message_hint": request.params["lti_message_hint"],
    }

    return HTTPFound(
        location=f"https://canvas.instructure.com/api/lti/authorize_redirect?{urlencode(params)}"
    )
