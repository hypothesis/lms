from pyramid.view import view_config


@view_config(
    request_method="GET",
    route_name="onedrive.filepicker.authorize",
    renderer="lms:templates/onedrive.html.jinja2",
)
def authorize(request):
    return {}
