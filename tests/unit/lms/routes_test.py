from __future__ import unicode_literals

from unittest import mock

from lms import routes


class TestIncludeMe:
    def test_it_adds_some_routes(self):
        config = mock.MagicMock()

        routes.includeme(config)

        assert config.mock_calls == [
            mock.call.add_route("index", "/"),
            mock.call.add_route("feature_flags_test", "/flags/test"),
            mock.call.add_route("welcome", "/welcome"),
            mock.call.add_route("assets", "/assets/*subpath"),
            mock.call.add_route("status", "/_status"),
            mock.call.add_route("favicon", "/favicon.ico"),
            mock.call.add_route("login", "/login"),
            mock.call.add_route("logout", "/logout"),
            mock.call.add_route("reports", "/reports"),
            mock.call.add_route("config_xml", "/config_xml"),
            mock.call.add_route(
                "module_item_configurations",
                "/module_item_configurations",
                factory="lms.resources.LTILaunchResource",
            ),
            mock.call.add_route(
                "lti_launches",
                "/lti_launches",
                factory="lms.resources.LTILaunchResource",
            ),
            mock.call.add_route(
                "content_item_selection",
                "/content_item_selection",
                factory="lms.resources.LTILaunchResource",
            ),
            mock.call.add_route(
                "canvas_oauth_callback",
                "/canvas_oauth_callback",
                factory="lms.resources.CanvasOAuth2RedirectResource",
            ),
            mock.call.add_route(
                "canvas_api.authorize",
                "/api/canvas/authorize",
                factory="lms.resources.CanvasOAuth2RedirectResource",
            ),
            mock.call.add_route(
                "canvas_api.courses.files.list", "/api/canvas/courses/{course_id}/files"
            ),
            mock.call.add_route(
                "canvas_api.files.via_url", "/api/canvas/files/{file_id}/via_url"
            ),
            mock.call.add_route(
                "canvas_api.sync", "/api/canvas/sync", request_method="POST"
            ),
            mock.call.add_route("lti_api.submissions.record", "/api/lti/submissions"),
            mock.call.add_route(
                "lti_api.result.read", "/api/lti/result", request_method="GET"
            ),
            mock.call.add_route(
                "lti_api.result.record", "/api/lti/result", request_method="POST"
            ),
        ]
