from unittest import mock

import pytest

from lms.resources import LTILaunchResource
from lms.services.group_info_upsert import GroupInfoUpsert
from lms.views.decorators._helpers import upsert_group_info


class TestUpsertGroupInfo:
    def test_it(self, context, group_info_upsert, params, pyramid_request):
        upsert_group_info(context, pyramid_request)

        assert group_info_upsert.call_args_list == [
            mock.call(
                context.h_authority_provided_id, "TEST_OAUTH_CONSUMER_KEY", **params
            )
        ]

    def test_it_defaults_to_None_if_request_params_are_missing(
        self, context, group_info_upsert, params, pyramid_request
    ):
        pyramid_request.params = {}

        upsert_group_info(context, pyramid_request)

        assert group_info_upsert.call_args_list == [
            mock.call(
                context.h_authority_provided_id,
                "TEST_OAUTH_CONSUMER_KEY",
                **{param: None for param in params.keys()}
            )
        ]

    @pytest.fixture
    def context(self):
        return mock.create_autospec(LTILaunchResource, instance=True, spec_set=True)

    @pytest.fixture
    def params(self):
        return dict(
            context_id="test_context_id",
            context_title="test_context_title",
            context_label="test_context_label",
            tool_consumer_info_product_family_code="test_tool_consumer_info_product_family_code",
            tool_consumer_info_version="test_tool_consumer_info_version",
            tool_consumer_instance_name="test_tool_consumer_instance_name",
            tool_consumer_instance_description="test_tool_consumer_instance_description",
            tool_consumer_instance_url="test_tool_consumer_instance_url",
            tool_consumer_instance_contact_email="test_tool_consumer_instance_contact_email",
            tool_consumer_instance_guid="test_tool_consumer_instance_guid",
            custom_canvas_api_domain="test_custom_canvas_api_domain",
            custom_canvas_course_id="test_custom_canvas_course_id",
        )

    @pytest.fixture(autouse=True)
    def group_info_upsert(self, pyramid_config):
        group_info_upsert = mock.create_autospec(
            GroupInfoUpsert, instance=True, spec_set=True
        )
        pyramid_config.register_service(group_info_upsert, name="group_info_upsert")
        return group_info_upsert

    @pytest.fixture
    def pyramid_request(self, params, pyramid_request):
        pyramid_request.params = params
        return pyramid_request
