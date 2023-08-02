from unittest.mock import create_autospec

import pytest

from lms.product.plugin.grading import GradingPlugin
from lms.resources._js_config import JSConfig
from tests import factories


class TestGradingPlugin:
    @pytest.mark.usefixtures("user_is_instructor")
    @pytest.mark.parametrize("is_gradable", [True, False])
    def test_configure_grading_for_launch_instructor(
        self, plugin, is_gradable, js_config, pyramid_request, grading_info_service
    ):
        assignment = factories.Assignment(is_gradable=is_gradable)

        plugin.configure_grading_for_launch(pyramid_request, js_config, assignment)

        js_config.enable_instructor_toolbar.assert_called_with(
            enable_grading=is_gradable
        )
        grading_info_service.upsert_from_request.assert_not_called()

    @pytest.mark.usefixtures("user_is_learner")
    def test_configure_grading_for_launch_learner(
        self, plugin, js_config, pyramid_request, grading_info_service
    ):
        assignment = factories.Assignment()

        plugin.configure_grading_for_launch(pyramid_request, js_config, assignment)

        grading_info_service.upsert_from_request.assert_called_once_with(
            pyramid_request
        )
        js_config.enable_instructor_toolbar.assert_not_called()

    @pytest.fixture
    def js_config(self):
        return create_autospec(JSConfig, spec_set=True, instance=True)

    @pytest.fixture
    def plugin(self):
        return GradingPlugin()
