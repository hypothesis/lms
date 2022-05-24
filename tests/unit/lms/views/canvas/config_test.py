from lms.views.canvas.config import config_json, config_xml


class TestConfigXml:
    def test_it_renders_the_config_xml(self, pyramid_request):
        response = config_xml(pyramid_request)
        assert response is not None


class TestConfigJSON:
    def test_it(self, pyramid_request):
        config_dict = config_json(pyramid_request)

        assert config_dict == {
            "title": "Hypothesis",
            "description": "Hypothesis",
            "oidc_initiation_url": "http://example.com/lti/1.3/oidc",
            "target_link_uri": "http://example.com/lti_launches",
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
                                "target_link_uri": "http://example.com/content_item_selection",
                            },
                            {
                                "text": "Hypothesis",
                                "enabled": True,
                                "placement": "assignment_selection",
                                "message_type": "LtiDeepLinkingRequest",
                                "target_link_uri": "http://example.com/content_item_selection",
                            },
                        ],
                    },
                }
            ],
            "public_jwk_url": "http://example.com/lti/1.3/jwks",
            "custom_fields": {
                "custom_canvas_course_id": "$Canvas.course.id",
                "custom_canvas_api_domain": "$Canvas.api.domain",
                "custom_canvas_user_id": "$Canvas.user.id",
            },
            "scopes": [
                "https://purl.imsglobal.org/spec/lti-ags/scope/score",
                "https://purl.imsglobal.org/spec/lti-ags/scope/result.readonly",
                "https://purl.imsglobal.org/spec/lti-nrps/scope/contextmembership.readonly",
                "https://purl.imsglobal.org/spec/lti-ags/scope/lineitem.readonly",
                "https://purl.imsglobal.org/spec/lti-ags/scope/lineitem",
            ],
        }
