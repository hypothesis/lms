from pyramid.view import view_config


@view_config(
    route_name="canvas.v11.config",
    renderer="lms:templates/config.xml.jinja2",
    request_method="GET",
)
def config_xml(request):
    """Render the XML configuration."""
    request.response.content_type = "text/xml"

    return {
        "launch_url": request.route_url("lti_launches"),
        "content_item_url": request.route_url("content_item_selection"),
    }
