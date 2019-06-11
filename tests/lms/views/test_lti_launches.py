import unittest.mock as mock

import pytest

from lms.views.lti_launches import lti_launches
from lms.exceptions import MissingLTILaunchParamError
from lms.resources import LTILaunchResource
from tests.lms.conftest import unwrap


# The `lti_launches` view function is wrapped in a series of decorators which
# handle authorization and creating the user/group for the current course.
#
# In these tests we only want to test the view function itself, so extract that
# from the decorated function.
lti_launches = unwrap(lti_launches)


# TODO write tests for student case
@pytest.mark.usefixtures("find_token_by_user_id")
class TestLtiLaunches:
    def test_it_renders_the_iframe_when_the_url_is_present_in_the_params(
        self, lti_launch_request, jwt, user
    ):
        lti_launch_request.params["url"] = "https://example.com"
        value = lti_launches(lti_launch_request, jwt, user)
        assert "iframe" in value.body.decode()
        assert "example.com" in value.body.decode()

    def test_render_the_form_when_the_url_is_not_present_in_the_params(
        self, lti_launch_request, jwt, user
    ):
        lti_launch_request.params["resource_link_id"] = "test_link_id"
        value = lti_launches(lti_launch_request, jwt, user)
        assert "<form" in value.body.decode()

    def test_render_the_document_if_configured(
        self, lti_launch_request, module_item_configuration, jwt, user
    ):
        lti_launch_request.db.add(module_item_configuration)
        lti_launch_request.db.flush()
        lti_launch_request.params[
            "resource_link_id"
        ] = module_item_configuration.resource_link_id
        lti_launch_request.params[
            "tool_consumer_instance_guid"
        ] = module_item_configuration.tool_consumer_instance_guid
        value = lti_launches(lti_launch_request, jwt, user)
        assert "iframe" in value.body.decode()
        assert "example.com" in value.body.decode()

    def test_render_unauthorized_for_students(
        self, lti_launch_request, module_item_configuration, jwt, user
    ):
        lti_launch_request.params[
            "resource_link_id"
        ] = module_item_configuration.resource_link_id
        lti_launch_request.params[
            "tool_consumer_instance_guid"
        ] = module_item_configuration.tool_consumer_instance_guid
        lti_launch_request.params["roles"] = "urn:lti:role:ims/lis/Learner"
        value = lti_launches(lti_launch_request, jwt, user)
        assert "This page has not yet been configured" in value.body.decode()

    def test_raises_for_missing_context_id_param(self, lti_launch_request, jwt, user):
        del lti_launch_request.params["context_id"]

        with pytest.raises(
            MissingLTILaunchParamError,
            match="Required data param for LTI launch missing: context_id",
        ):
            lti_launches(lti_launch_request, jwt, user)

    def test_raises_for_missing_resource_link_id_param(
        self, lti_launch_request, jwt, user
    ):
        del lti_launch_request.params["resource_link_id"]
        with pytest.raises(
            MissingLTILaunchParamError,
            match="Required data param for LTI launch missing: resource_link_id",
        ):
            lti_launches(lti_launch_request, jwt, user)

    def test_raises_for_missing_roles_param(
        self, lti_launch_request, module_item_configuration, jwt, user
    ):
        del lti_launch_request.params["roles"]
        with pytest.raises(
            MissingLTILaunchParamError,
            match="Required data param for LTI launch missing: roles",
        ):
            lti_launches(lti_launch_request, jwt, user)

    def test_raises_for_tool_consumer_instance_guid_param(
        self, lti_launch_request, jwt, user
    ):
        del lti_launch_request.params["tool_consumer_instance_guid"]
        with pytest.raises(
            MissingLTILaunchParamError,
            match="Required data param for LTI launch missing: tool_consumer_instance_guid",
        ):
            lti_launches(lti_launch_request, jwt, user)

    def test_raises_for_missing_oauth_consumer_key_param(
        self, lti_launch_request, jwt, user
    ):
        del lti_launch_request.params["oauth_consumer_key"]

        with pytest.raises(
            MissingLTILaunchParamError,
            match="Required data param for LTI launch missing: oauth_consumer_key",
        ):
            lti_launches(lti_launch_request, jwt, user)


@pytest.fixture
def lti_launch_request(lti_launch_request):
    lti_launch_request.params["resource_link_id"] = "test_link_id"

    lti_launch_request.context = mock.create_autospec(
        LTILaunchResource,
        spec_set=True,
        instance=True,
        rpc_server_config={},
        hypothesis_config={},
        provisioning_enabled=True,
    )

    return lti_launch_request


@pytest.fixture
def jwt():
    return "test_jwt"


@pytest.fixture
def user():
    return mock.Mock(spec_set=["id", "lms_guid"], id=42)


@pytest.fixture
def find_token_by_user_id(patch):
    return patch("lms.views.lti_launches.find_token_by_user_id")
