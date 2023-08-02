from unittest.mock import create_autospec

import pytest

from lms.product.plugin.grading import GradingPlugin
from lms.resources._js_config import JSConfig
from tests import factories


class TestGradingPlugin:
    @pytest.mark.usefixtures("user_is_instructor")
    @pytest.mark.parametrize("lti_v13", [True, False])
    @pytest.mark.parametrize("is_gradable", [True, False])
    def test_configure_grading_for_launch_instructor(
        self,
        request,
        plugin,
        is_gradable,
        js_config,
        pyramid_request,
        grading_info_service,
    ):
        assignment = factories.Assignment(is_gradable=is_gradable)

        plugin.configure_grading_for_launch(pyramid_request, js_config, assignment)

        js_config.enable_instructor_toolbar.assert_called_with(
            enable_grading=is_gradable
        )

        if lti_v13:
            _ = request.getfixturevalue("with_lti_13")

        if is_gradable:
            expected_students = [
                {
                    "userid": f"acct:{grading_info.h_username}@lms.hypothes.is",
                    "displayName": grading_info.h_display_name,
                    "lmsId": grading_info.user_id,
                    "LISResultSourcedId": grading_info.lis_result_sourcedid
                    if not lti_v13
                    else grading_info.user_id,
                    "LISOutcomeServiceUrl": pyramid_request.lti_params[
                        "lis_outcome_service_url"
                    ],
                }
                for grading_info in grading_info_service.get_by_assignment.return_value
            ]
            grading_info_service.get_by_assignment.assert_called_once_with(
                context_id="test_course_id",
                application_instance=pyramid_request.lti_user.application_instance,
                resource_link_id="TEST_RESOURCE_LINK_ID",
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
