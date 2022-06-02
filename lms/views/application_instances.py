from pyramid.view import view_config


@view_config(
    route_name="welcome",
    request_method="POST",
    renderer=(
        "lms:templates/application_instances/create_application_instance.html.jinja2"
    ),
)
def create_application_instance(request):
    """Create application instance in the database and respond with key and secret."""
    developer_key = request.params["developer_key"].strip()
    developer_secret = request.params["developer_secret"].strip()

    instance = request.find_service(
        name="application_instance"
    ).create_application_instance(
        request.params["lms_url"],
        request.params["email"],
        developer_key,
        developer_secret,
        settings={
            "canvas": {
                "sections_enabled": False,
                "groups_enabled": bool(developer_key),
            }
        },
    )

    return {
        "consumer_key": instance.consumer_key,
        "shared_secret": instance.shared_secret,
    }


@view_config(
    route_name="welcome",
    renderer="lms:templates/application_instances/new_application_instance.html.jinja2",
)
def new_application_instance(_):
    """Render the form where users enter the lms url and email."""
    return {}
