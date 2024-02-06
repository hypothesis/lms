"""
Configuration views for Canvas.

These views allow an admin user to paste in a URL and have Hypothesis automatically
configured in Canvas.
"""
from pyramid.view import view_config


@view_config(
    route_name="canvas.v11.config",
    renderer="lms:templates/config.xml.jinja2",
    request_method="GET",
)
def config_xml(request):
    """
    Render the configuration for LTI1.1 as an XML.

    https://canvas.instructure.com/doc/api/file.tools_xml.html
    """
    request.response.content_type = "text/xml"

    return {
        "launch_url": request.route_url("lti_launches"),
        "content_item_url": request.route_url("content_item_selection"),
    }


@view_config(
    route_name="canvas.v13.config",
    renderer="json",
    request_method="GET",
)
def config_json(request):
    """
    Return tool configuration for Canvas installs as a json document.

    https://canvas.instructure.com/doc/api/file.lti_dev_key_config.html#anatomy-of-a-json-configuration
    """
    return {
        "title": "Hypothesis",
        "description": "Hypothesis",
        "oidc_initiation_url": request.route_url("lti.oidc"),
        "target_link_uri": request.route_url("lti_launches"),
        "extensions": [
            {
                "platform": "canvas.instructure.com",
                "privacy_level": "public",
                "settings": {
                    "placements": [
                        {
                            "text": "Hypothesis",
                            "enabled": True,
                            "placement": "link_selection",
                            "message_type": "LtiDeepLinkingRequest",
                            "target_link_uri": request.route_url(
                                "content_item_selection"
                            ),
                            "selection_width": 800,
                            "selection_height": 600,
                        },
                        {
                            "text": "Hypothesis",
                            "enabled": True,
                            "placement": "assignment_selection",
                            "message_type": "LtiDeepLinkingRequest",
                            "target_link_uri": request.route_url(
                                "content_item_selection"
                            ),
                            "selection_width": 800,
                            "selection_height": 600,
                        },
                    ],
                },
            }
        ],
        "public_jwk_url": request.route_url("lti.jwks"),
        "custom_fields": {
            "custom_canvas_course_id": "$Canvas.course.id",
            "custom_canvas_api_domain": "$Canvas.api.domain",
            "custom_canvas_user_id": "$Canvas.user.id",
            "custom_display_name": "$Person.name.display",
        },
        "scopes": [
            "https://purl.imsglobal.org/spec/lti-ags/scope/score",
            "https://purl.imsglobal.org/spec/lti-ags/scope/result.readonly",
            "https://purl.imsglobal.org/spec/lti-nrps/scope/contextmembership.readonly",
            "https://purl.imsglobal.org/spec/lti-ags/scope/lineitem.readonly",
            "https://purl.imsglobal.org/spec/lti-ags/scope/lineitem",
        ],
    }
