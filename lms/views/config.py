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
def canvas_config_json(request):
    # https://canvas.instructure.com/doc/api/file.lti_dev_key_config.html
    config = _basic_lti_13_config(request)

    config["custom_fields"] = {
        "custom_canvas_course_id": "$Canvas.course.id",
        "custom_canvas_api_domain": "$Canvas.api.domain",
    }

    return config


def _basic_lti_13_config(request):
    lti_oidc_url = request.route_url("lti_oidc")
    launch_url = request.route_url("lti_launches")
    content_item_url = request.route_url("content_item_selection")
    jwts_url = request.route_url("jwts")
    from lms.views.openid import public_key

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
                            "message_type": "LtiDeepLinkingRequest",
                            "target_link_uri": content_item_url,
                        },
                        {
                            "text": "Assignment selection text",
                            "enabled": True,
                            "placement": "assignment_selection",
                            "message_type": "LtiDeepLinkingRequest",
                            "target_link_uri": content_item_url,
                        },
                    ],
                },
            }
        ],
        "public_jwk_url": jwts_url,  # , Canvas doesn't like this
        "public_jwk": public_key,
    }
