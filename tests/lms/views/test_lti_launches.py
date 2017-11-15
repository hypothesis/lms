from lms.views import lti_launches


# TODO write tests for student case
class TestApplicationInstance(object):
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
        lti_launch_request.params['resource_link_id'] = module_item_configuration.resource_link_id
        lti_launch_request.params['tool_consumer_instance_guid'] = (
            module_item_configuration.tool_consumer_instance_guid
        )
        value = lti_launches(lti_launch_request)
        assert 'iframe' in value.body.decode()
        assert 'example.com' in value.body.decode()
