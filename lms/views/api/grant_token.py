import datetime
from urllib.parse import urlparse

import jwt
from pyramid.view import view_config


@view_config(permission="api", renderer="json", route_name="api.grant_token")
def grant_token(request):
    """
    Return a grant token that the Hypothesis client can use to log in to H.
    """

    # TODO - Avoid duplicating this code from `JSConfig._grant_token`.
    api_url = request.registry.settings["h_api_url_public"]
    authority = request.registry.settings["h_authority"]
    h_user = request.lti_user.h_user
    now = datetime.datetime.utcnow()

    claims = {
        "aud": urlparse(api_url).hostname,
        "iss": request.registry.settings["h_jwt_client_id"],
        "sub": h_user.userid(authority),
        "nbf": now,
        "exp": now + datetime.timedelta(minutes=5),
    }

    return {
        "grant_token": jwt.encode(
            claims,
            request.registry.settings["h_jwt_client_secret"],
            algorithm="HS256",
        )
    }
