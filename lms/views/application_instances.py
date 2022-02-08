from pyramid.view import view_config

from lms.models import ApplicationInstance


@view_config(
    route_name="welcome",
    request_method="POST",
    renderer=(
        "lms:templates/application_instances/create_application_instance.html.jinja2"
    ),
)
def create_application_instance(request):
    """Create application instance in the databse and respond with key and secret."""

    # Default developer_key and developer_secret to None rather than letting
    # them be empty strings.
    developer_key = request.params["developer_key"].strip()
    developer_secret = request.params["developer_secret"].strip()

    # If either one of developer_key or developer_secret is missing, then we
    # don't save the other one either.
    if not developer_key or not developer_secret:
        developer_key = None
        developer_secret = None

    instance = ApplicationInstance.build_from_lms_url(
        request.params["lms_url"],
        request.params["email"],
        developer_key,
        developer_secret,
        request.registry.settings["aes_secret"],
        settings={
            "canvas": {
                "sections_enabled": False,
                "groups_enabled": bool(developer_key),
            }
        },
    )
    request.db.add(instance)

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
