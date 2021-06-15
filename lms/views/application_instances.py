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

    ai = request.find_service(name="application_instance").create(
        request.params["lms_url"],
        request.params["email"],
        request.params["developer_key"].strip(),
        request.params["developer_secret"].strip(),
        request.registry.settings["aes_secret"],
    )
    return {
        "consumer_key": ai.consumer_key,
        "shared_secret": ai.shared_secret,
    }


@view_config(
    route_name="welcome",
    renderer="lms:templates/application_instances/new_application_instance.html.jinja2",
)
def new_application_instance(_):
    """Render the form where users enter the lms url and email."""
    return {}
