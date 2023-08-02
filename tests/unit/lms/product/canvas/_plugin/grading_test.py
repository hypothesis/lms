from unittest.mock import create_autospec, sentinel

import pytest

from lms.product.canvas._plugin.grading import CanvasGradingPlugin
from lms.resources._js_config import JSConfig
from tests import factories


class TestGradingPlugin:
    @pytest.mark.usefixtures("user_is_learner", "with_student_grading_id")
    def test_configure_grading_for_launch_adds_speed_grader_settings(
        self, plugin, js_config, pyramid_request
    ):
        assignment = factories.Assignment(is_gradable=True)

        plugin.configure_grading_for_launch(pyramid_request, js_config, assignment)

        js_config.add_canvas_speedgrader_settings.assert_called_once_with(
            assignment.document_url
        )

    @pytest.mark.usefixtures("user_is_instructor", "with_student_grading_id")
    def test_configure_grading_for_launch_no_speed_grader_for_instructor(
        self, plugin, js_config, pyramid_request
    ):
        assignment = factories.Assignment(is_gradable=True)

        plugin.configure_grading_for_launch(pyramid_request, js_config, assignment)

        js_config.add_canvas_speedgrader_settings.assert_not_called()

    @pytest.mark.usefixtures("user_is_learner", "with_student_grading_id")
    def test_configure_grading_for_launch_no_speedgrader_non_gradable(
        self, plugin, js_config, pyramid_request
    ):
        assignment = factories.Assignment(is_gradable=False)

        plugin.configure_grading_for_launch(pyramid_request, js_config, assignment)

        js_config.add_canvas_speedgrader_settings.assert_not_called()

    @pytest.mark.usefixtures("user_is_learner")
    def test_configure_grading_for_launch_no_speed_grader_no_grading_id(
        self, plugin, js_config, pyramid_request
    ):
        assignment = factories.Assignment(is_gradable=True)

        plugin.configure_grading_for_launch(pyramid_request, js_config, assignment)

        js_config.add_canvas_speedgrader_settings.assert_not_called()

    @pytest.mark.parametrize("focused_user", [None, sentinel.focused_user])
    def test_configure_grading_for_launch_sets_focused_user(
        self, pyramid_request, focused_user, js_config, plugin
    ):
        pyramid_request.params["focused_user"] = focused_user

        plugin.configure_grading_for_launch(
            pyramid_request, js_config, factories.Assignment()
        )

        if focused_user:
            js_config.set_focused_user.assert_called_once_with(focused_user)
        else:
            js_config.set_focused_user.assert_not_called()

    def test_factory(self, pyramid_request):
        plugin = CanvasGradingPlugin.factory(sentinel.context, pyramid_request)
        assert isinstance(plugin, CanvasGradingPlugin)

    @pytest.fixture
    def with_student_grading_id(self, pyramid_request):
        # This shows that a student has launched the assignment and a grade
        # is assignable to them
        pyramid_request.lti_params["lis_result_sourcedid"] = "9083745892345834h5"

    @pytest.fixture
    def js_config(self):
        return create_autospec(JSConfig, spec_set=True, instance=True)

    @pytest.fixture
    def plugin(self):
        return CanvasGradingPlugin()
