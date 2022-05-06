from unittest import mock
from unittest.mock import create_autospec, sentinel

import pytest
from h_matchers import Any

from lms.models import ApplicationInstance
from lms.resources import LTILaunchResource
from lms.resources._js_config import JSConfig
from lms.views.lti.deep_linking import DeepLinkingFieldsViews, deep_linking_launch


@pytest.mark.usefixtures("application_instance_service", "lti_h_service")
class TestDeepLinkingLaunch:
    def test_it(
        self, context, pyramid_request, lti_h_service, application_instance_service
    ):
        application_instance_service.get_current.return_value = create_autospec(
            ApplicationInstance, spec_set=True, instance=True
        )

        deep_linking_launch(context, pyramid_request)

        application_instance_service.get_current.return_value.update_lms_data.assert_called_once_with(
            pyramid_request.params
        )
        context.get_or_create_course.assert_called_once_with()
        lti_h_service.sync.assert_called_once_with(
            [context.h_group], pyramid_request.params
        )
        context.js_config.enable_file_picker_mode.assert_called_once_with(
            form_action="TEST_CONTENT_ITEM_RETURN_URL",
            form_fields={
                "lti_message_type": "ContentItemSelection",
                "lti_version": "TEST_LTI_VERSION",
            },
        )
        context.js_config.add_deep_linking_api.assert_not_called()

    def test_it_enables_content_item_selection_mode_lti_v13(
        self, context, pyramid_request, application_instance
    ):
        application_instance.lti_registration_id = 100

        deep_linking_launch(context, pyramid_request)

        context.js_config.add_deep_linking_api.assert_called_once()

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.parsed_params = {
            "content_item_return_url": "TEST_CONTENT_ITEM_RETURN_URL",
            "lti_version": "TEST_LTI_VERSION",
        }
        return pyramid_request

    @pytest.fixture
    def context(self):
        context = mock.create_autospec(LTILaunchResource, spec_set=True, instance=True)
        context.js_config = mock.create_autospec(JSConfig, spec_set=True, instance=True)
        return context


@pytest.mark.usefixtures("application_instance_service")
class TestDeepLinkingFieldsView:
    def test_it(self, ltia_http_service, application_instance, pyramid_request):
        fields = DeepLinkingFieldsViews(
            pyramid_request
        ).file_picker_to_form_fields_v13()

        expected_url = Any.url.matching("http://example.com/lti_launches").with_query()
        ltia_http_service.sign.assert_called_once_with(
            {
                "https://purl.imsglobal.org/spec/lti/claim/deployment_id": application_instance.deployment_id,
                "https://purl.imsglobal.org/spec/lti/claim/message_type": "LtiDeepLinkingResponse",
                "https://purl.imsglobal.org/spec/lti/claim/version": "1.3.0",
                "https://purl.imsglobal.org/spec/lti-dl/claim/content_items": [
                    {"type": "ltiResourceLink", "url": expected_url}
                ],
                "https://purl.imsglobal.org/spec/lti-dl/claim/data": sentinel.deep_linking_settings,
            }
        )
        assert fields["JWT"] == ltia_http_service.sign.return_value

    @pytest.mark.parametrize(
        "content,output_params",
        [
            (
                {"type": "file", "file": {"id": 1}},
                {"canvas_file": "true", "file_id": "1"},
            ),
            (
                {"type": "url", "url": "https://example.com"},
                {"url": "https://example.com"},
            ),
        ],
    )
    @pytest.mark.parametrize("extra_params", ({}, {"extra": "value"}))
    def test_it_with_different_file_types(
        self, content, output_params, extra_params, ltia_http_service, pyramid_request
    ):
        pyramid_request.parsed_params.update(
            {"content": content, "extra_params": extra_params}
        )

        DeepLinkingFieldsViews(pyramid_request).file_picker_to_form_fields_v13()

        output_params.update(extra_params)
        ltia_http_service.sign.assert_called_once_with(
            Any.dict.containing(
                {
                    "https://purl.imsglobal.org/spec/lti-dl/claim/content_items": [
                        Any.dict.containing({"url": Any.url.with_query(output_params)})
                    ]
                }
            )
        )

    def test_it_with_unknown_file_type(self, pyramid_request):
        pyramid_request.parsed_params.update({"content": {"type": "other"}})

        with pytest.raises(ValueError):
            DeepLinkingFieldsViews(pyramid_request).file_picker_to_form_fields_v13()

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.parsed_params = {
            "deep_linking_settings": sentinel.deep_linking_settings,
            "content": {"type": "url", "url": "https://example.com"},
            "extra_params": {},
        }
        return pyramid_request
