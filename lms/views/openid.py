from urllib.parse import urlencode

from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config


@view_config(
    route_name="lti_oidc",
    request_method=("POST", "GET"),  ## BB get, canvas POST
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


@view_config(
    route_name="jwts",
    request_method="GET",
    renderer="json",
)
def jwts(request):
    # TODO either document how to generate from a private key
    # or take from env vars
    # or generate on startup
    return {
        "kty": "RSA",
        "alg": "RS256",
        "e": "AQAB",
        "kid": "a70262c4-181e-4d57-8056-d6d02a264284",
        "n": "mVcb5I6EOQi4Z2kFMR4lCNS8dUATfGMm3GiDUDUUIE8RS6swQQjlN72vZxuyZmi07755B9BgvFvCtni4rrUNJixXiaKpE_XrFKSKTJ0RiMCp76fOYG7hTJF3O5fZ42j6mUsEAyr9zV1AClQZUOVz2SN0pRCVxf8HC7lllwPfwLUXjkgHf8yBmffw_oAZLCgfWgRCS2AyzfMFMyxAsCx8gAFvYxroh47kAfR-Qy4No2GbUkbWbhEUZwwnHe-zgMoa1M_LMx8-_hZXjOlOGoDskoTWpZ9QDFWsC45-JlndGWkgnDqBF6F4BCY-jrvafeP4lRsW5O1ruwut_G6zwN0xbw",
        "use": "sig",
    }
