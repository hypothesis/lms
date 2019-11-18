from lms.views.basic_lti_launch import ConfigureModuleItemView


class TestConfigureModuleItem:
    def test_it_saves_the_assignments_document_url_to_the_db(
        self, context, pyramid_request, ModuleItemConfiguration
    ):
        pyramid_request.parsed_params = {
            "document_url": "TEST_DOCUMENT_URL",
            "resource_link_id": "TEST_RESOURCE_LINK_ID",
            "tool_consumer_instance_guid": "TEST_TOOL_CONSUMER_INSTANCE_GUID",
        }

        ConfigureModuleItemView(context, pyramid_request).configure_module_item()

        ModuleItemConfiguration.set_document_url.assert_called_once_with(
            pyramid_request.db,
            "TEST_TOOL_CONSUMER_INSTANCE_GUID",
            "TEST_RESOURCE_LINK_ID",
            "TEST_DOCUMENT_URL",
        )

    def test_it_configures_via_url(self, context, pyramid_request, via_url):
        pyramid_request.parsed_params = {
            "document_url": "TEST_DOCUMENT_URL",
            "resource_link_id": "TEST_RESOURCE_LINK_ID",
            "tool_consumer_instance_guid": "TEST_TOOL_CONSUMER_INSTANCE_GUID",
        }

        ConfigureModuleItemView(context, pyramid_request).configure_module_item()

        via_url.assert_called_once_with(pyramid_request, "TEST_DOCUMENT_URL")
        assert context.js_config["urls"]["via_url"] == via_url.return_value
