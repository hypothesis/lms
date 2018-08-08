from lms.views.lti_launches import lti_launches

import pytest

from lms.exceptions import MissingLTILaunchParamError

# TODO write tests for student case
class TestLtiLaunches(object):
    def test_it_renders_the_iframe_when_the_url_is_present_in_the_params(self, lti_launch_request):
        lti_launch_request.params['url'] = 'https://example.com'
        value = lti_launches(lti_launch_request)
        assert 'iframe' in value.body.decode()
        assert 'example.com' in value.body.decode()

    def test_render_the_form_when_the_url_is_not_present_in_the_params(self, lti_launch_request):
        lti_launch_request.params['resource_link_id'] = 'test_link_id'
        value = lti_launches(lti_launch_request)
        assert '<form' in value.body.decode()

    def test_render_the_document_if_configured(self, lti_launch_request, module_item_configuration):
        lti_launch_request.db.add(module_item_configuration)
        lti_launch_request.db.flush()
        lti_launch_request.params['resource_link_id'] = module_item_configuration.resource_link_id
        lti_launch_request.params['tool_consumer_instance_guid'] = (
            module_item_configuration.tool_consumer_instance_guid
        )
        value = lti_launches(lti_launch_request)
        assert 'iframe' in value.body.decode()
        assert 'example.com' in value.body.decode()

    def test_render_unauthorized_for_students(self, lti_launch_request, module_item_configuration):
        lti_launch_request.params['resource_link_id'] = module_item_configuration.resource_link_id
        lti_launch_request.params['tool_consumer_instance_guid'] = (
            module_item_configuration.tool_consumer_instance_guid
        )
        lti_launch_request.params['roles'] = 'urn:lti:role:ims/lis/Learner'
        value = lti_launches(lti_launch_request)
        assert 'This page has not yet been configured' in value.body.decode()

    def test_raises_for_missing_context_id_param(self, lti_launch_request):
        del lti_launch_request.params["context_id"]

        with pytest.raises(MissingLTILaunchParamError, match="LTI data parameter context_id is required for launch."):
            lti_launches(lti_launch_request)

    def test_raises_for_missing_resource_link_id_param(self, lti_launch_request):
        with pytest.raises(MissingLTILaunchParamError, match="LTI data parameter resource_link_id is required for launch."):
            lti_launches(lti_launch_request)

    def test_raises_for_missing_roles_param(self, lti_launch_request, module_item_configuration):
        del lti_launch_request.params['roles']
        with pytest.raises(MissingLTILaunchParamError, match='LTI data parameter roles is required for launch.'):
            lti_launches(lti_launch_request)
