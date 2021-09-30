from pyramid.view import view_config


@view_config(
    request_method="GET",
    route_name="onedrive.filepicker.redirect_uri",
    renderer="lms:templates/onedrive.html.jinja2",
)
def redirect_uri(_request):
    """
    Return a basic HTML page with One Drive's JS SDK loaded.

    This view's URL is provided to One Drive's frontend config as target to open the filepicker in.
    """
    return {}


@view_config(
    request_method="GET",
    route_name="onedrive.filepicker.verify_domain",
    renderer="json",
)
def verify_domain(request):
    return {
        "associatedApplications": [
            {"applicationId": request.registry.settings["onedrive_client_id"]}
        ]
    }
