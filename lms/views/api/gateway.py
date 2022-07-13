from pyramid.view import view_config

from lms.security import Permissions


@view_config(
    request_method="POST",
    permission=Permissions.API,
    renderer="json",
    route_name="api.gateway.h.lti"
)
def h_lti(request):
    """
    Provide tokens and information to allow customers to query H.

    We expect the user to authenticate with us using an LTI launch.
    """

    # Add API end-point details
    h_api_url = request.registry.settings["h_api_url_public"]
    return {
        "h_api": {
            # These sections are arranged so you can use
            # `requests.Request.request(**data)` and make the correct request
            "list_endpoints": {
                # List the API end-points
                "method": "GET",
                "url": h_api_url,
                "headers": {"Accept": "application/vnd.hypothesis.v2+json"},
            },
            "exchange_grant_token": {
                # Exchange our token for access and refresh tokens
                "method": "POST",
                "url": h_api_url + "token",
                "headers": {
                    "Accept": "application/vnd.hypothesis.v2+json",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                "data": {
                    # Generate a short-lived login token for the Hypothesis client
                    "assertion": request.find_service(
                        name="grant_token"
                    ).generate_token(request.lti_user.h_user),
                    "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                },
            },
        }
    }
