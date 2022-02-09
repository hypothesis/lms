from pyramid.view import view_config


@view_config(
    route_name="config_xml",
    renderer="lms:templates/config.xml.jinja2",
    request_method="GET",
)
def config_xml(request):
    """Render the XML configuration as XML."""
    request.response.content_type = "text/xml"

    return {
        "launch_url": request.route_url("lti_launches"),
        "content_item_url": request.route_url("content_item_selection"),
    }


@view_config(
    route_name="canvas_config_json",
    renderer="json",
    request_method="GET",
)
def config_json(request):
    config = _basic_lti_13_config(request)

    config["custom_fields"] = {
        "custom_canvas_course_id": "$Canvas.course.id",
        "custom_canvas_api_domain": "$Canvas.api.domain",
    }

    return config


def _basic_lti_13_config(request):
    lti_oidc_url = request.route_url("lti_oidc")
    launch_url = request.route_url("lti_launches")
    jwts_url = request.route_url("jwts")

    return {
        "title": "Hypothesis (title)",
        "description": "Hypothesis (description)",
        "oidc_initiation_url": lti_oidc_url,
        "target_link_uri": launch_url,
        "extensions": [
            {
                "domain": "thebesttool.com",
                "tool_id": "the-best-tool",
                "platform": "canvas.instructure.com",
                "privacy_level": "public",
                "settings": {
                    "text": "Launch The Best Tool",
                    "icon_url": "https://some.icon.url/tool-level.png",
                    "placements": [
                        {
                            "text": "Link selection placement text",
                            "enabled": True,
                            "placement": "link_selection",
                            "message_type": "LtiResourceLinkRequest",
                            "url": launch_url,
                        },
                        {
                            "text": "Assignment selection text",
                            "enabled": True,
                            "placement": "assignment_selection",
                            "message_type": "LtiResourceLinkRequest",
                            "url": launch_url,
                        },
                    ],
                },
            }
        ],
        "public_jwk": jwts_url,
    }
