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
                                "selection_width": 800,
                                "selection_height": 600,
                            },
                            {
                                "text": "Hypothesis",
                                "enabled": True,
                                "placement": "assignment_selection",
                                "message_type": "LtiDeepLinkingRequest",
                                "target_link_uri": "http://example.com/content_item_selection",
                                "selection_width": 800,
                                "selection_height": 600,
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
                "custom_display_name": "$Person.name.display",
                "custom_context_id_history": "$Context.id.history",
                "custom_course_starts": "$Canvas.course.startAt",
                "custom_course_ends": "$Canvas.course.endAt",
                "custom_term_id": "$Canvas.term.id",
                "custom_term_name": "$Canvas.term.name",
                "custom_term_start": "$Canvas.term.startAt",
                "custom_term_end": "$Canvas.term.endAt",
                "custom_assignment_id": "$Canvas.assignment.id",
                "custom_allowed_attempts": "$Canvas.assignment.allowedAttempts",
                "custom_submitted_attempts": "$Canvas.assignment.submission.studentAttempts",
            },
            "scopes": [
                "https://purl.imsglobal.org/spec/lti-ags/scope/score",
                "https://purl.imsglobal.org/spec/lti-ags/scope/result.readonly",
                "https://purl.imsglobal.org/spec/lti-nrps/scope/contextmembership.readonly",
                "https://purl.imsglobal.org/spec/lti-ags/scope/lineitem.readonly",
                "https://purl.imsglobal.org/spec/lti-ags/scope/lineitem",
            ],
        }
