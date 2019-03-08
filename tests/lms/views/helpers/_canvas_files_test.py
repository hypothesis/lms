import pytest

from lms.views.helpers import canvas_files_available
from lms.services import ConsumerKeyError


class TestCanvasFilesAvailable:
    def test_it_gets_the_developer_key_for_the_oauth_consumer_key(
        self, pyramid_request, ai_getter
    ):
        canvas_files_available(pyramid_request)

        ai_getter.developer_key.assert_called_once_with("TEST_OAUTH_CONSUMER_KEY")

    @pytest.mark.parametrize(
        "developer_key,params,canvas_files_enabled",
        [
            # If the LMS appears to be Canvas (judged by the presence of the
            # custom_canvas_course_id LTI launch parameter) and we have a developer
            # key matching the oauth_consumer_key parameter then we enable Canvas
            # Files support.
            (
                "TEST_DEVELOPER_KEY",
                {
                    "oauth_consumer_key": "TEST_CONSUMER_KEY",
                    "custom_canvas_course_id": "FOO",
                },
                True,
            ),
            # If the LMS doesn't appear to be Canvas (judged by the absence of the
            # custom_canvas_course_id LTI launch parameter) then even if we have a
            # developer key matching the oauth_consumer_key parameter we still
            # don't enable Canvas Files support.
            ("TEST_DEVELOPER_KEY", {"oauth_consumer_key": "TEST_CONSUMER_KEY"}, False),
            # If the LMS appears to be Canvas (judged by the presence of the
            # custom_canvas_course_id LTI launch parameter) but we don't have a
            # developer key matching the oauth_consumer_key parameter then we don't
            # enable Canvas Files support.
            (
                None,
                {
                    "oauth_consumer_key": "TEST_CONSUMER_KEY",
                    "custom_canvas_course_id": "FOO",
                },
                False,
            ),
            # If there's no oauth_consumer_key then it returns False.
            (None, {"custom_canvas_course_id": "FOO"}, False),
        ],
    )
    def test_it_enables_or_disables_Canvas_Files_support(
        self, pyramid_request, ai_getter, developer_key, params, canvas_files_enabled
    ):
        ai_getter.developer_key.return_value = developer_key
        pyramid_request.params = params

        assert canvas_files_available(pyramid_request) == canvas_files_enabled

    def test_it_returns_False_if_the_oauth_consumer_key_is_unknown(
        self, pyramid_request, ai_getter
    ):
        ai_getter.developer_key.side_effect = ConsumerKeyError()
        pyramid_request.params = {
            "oauth_consumer_key": "TEST_CONSUMER_KEY",
            "custom_canvas_course_id": "FOO",
        }

        assert canvas_files_available(pyramid_request) is False

    def test_it_supports_passing_in_custom_params(self, pyramid_request):
        pyramid_request.params = {}
        params = {
            "oauth_consumer_key": "TEST_CONSUMER_KEY",
            "custom_canvas_course_id": "FOO",
        }

        assert canvas_files_available(pyramid_request, params=params) is True
