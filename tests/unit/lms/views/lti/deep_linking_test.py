import json
from datetime import datetime
from unittest.mock import create_autospec, patch, sentinel

import pytest
from freezegun import freeze_time
from h_matchers import Any

from lms.resources._js_config import JSConfig
from lms.views.lti.deep_linking import DeepLinkingFieldsViews, deep_linking_launch
from tests import factories


@pytest.mark.usefixtures("application_instance_service", "lti_h_service")
class TestDeepLinkingLaunch:
    def test_it(
        self,
        js_config,
        pyramid_request,
        lti_h_service,
        application_instance_service,
        course_service,
    ):
        deep_linking_launch(pyramid_request)

        application_instance_service.update_from_lti_params.assert_called_once_with(
            pyramid_request.lti_user.application_instance,
            pyramid_request.lti_params,
            pyramid_request.lti_params,
        )
        course_service.get_from_launch.assert_called_once_with(
            pyramid_request.product, pyramid_request.lti_params
        )
        lti_h_service.sync.assert_called_once_with(
            [course_service.get_from_launch.return_value], pyramid_request.params
        )
        js_config.enable_file_picker_mode.assert_called_once_with(
            form_action="TEST_CONTENT_ITEM_RETURN_URL",
            form_fields={
                "lti_message_type": "ContentItemSelection",
                "lti_version": "TEST_LTI_VERSION",
            },
        )
        js_config.add_deep_linking_api.assert_called_once()

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.parsed_params = {
            "content_item_return_url": "TEST_CONTENT_ITEM_RETURN_URL",
            "lti_version": "TEST_LTI_VERSION",
        }
        return pyramid_request

    @pytest.fixture
    def js_config(self):
        return create_autospec(JSConfig, spec_set=True, instance=True)


@pytest.mark.usefixtures("application_instance_service")
class TestDeepLinkingFieldsView:
    @freeze_time("2022-04-04")
    def test_it_for_v13(
        self,
        jwt_service,
        application_instance,
        views,
        _get_content_url_mock,
        uuid,
        LTIEvent,
        pyramid_request,
    ):
        fields = views.file_picker_to_form_fields_v13()

        jwt_service.encode_with_private_key.assert_called_once_with(
            {
                "exp": datetime(2022, 4, 4, 1, 0),
                "iat": datetime(2022, 4, 4, 0, 0),
                "iss": application_instance.lti_registration.client_id,
                "sub": application_instance.lti_registration.client_id,
                "aud": application_instance.lti_registration.issuer,
                "nonce": uuid.uuid4().hex,
                "https://purl.imsglobal.org/spec/lti/claim/deployment_id": application_instance.deployment_id,
                "https://purl.imsglobal.org/spec/lti/claim/message_type": "LtiDeepLinkingResponse",
                "https://purl.imsglobal.org/spec/lti/claim/version": "1.3.0",
                "https://purl.imsglobal.org/spec/lti-dl/claim/content_items": [
                    {
                        "type": "ltiResourceLink",
                        "url": _get_content_url_mock.return_value,
                    }
                ],
                "https://purl.imsglobal.org/spec/lti-dl/claim/data": sentinel.deep_linking_settings_data,
            }
        )
        LTIEvent.assert_called_once_with(
            request=pyramid_request,
            type=LTIEvent.Type.DEEP_LINKING,
            data={"document_url": _get_content_url_mock.return_value},
        )
        pyramid_request.registry.notify.has_call_with(LTIEvent.return_value)
        assert fields["JWT"] == jwt_service.encode_with_private_key.return_value

    @pytest.mark.usefixtures("LTIEvent")
    @pytest.mark.parametrize("settings", [None, {}, {"data": None}])
    def test_it_for_v13_missing_deep_linking_settings_data(
        self, jwt_service, views, pyramid_request, settings
    ):
        pyramid_request.parsed_params["deep_linking_settings"] = settings

        views.file_picker_to_form_fields_v13()

        jwt_service.encode_with_private_key.assert_called_once_with(
            message := Any.dict()
        )
        assert (
            "https://purl.imsglobal.org/spec/lti-dl/claim/data "
            not in message.last_matched()  # pylint: disable=unsupported-membership-test
        )

    def test_it_for_v11(self, views, _get_content_url_mock, pyramid_request, LTIEvent):
        _get_content_url_mock.return_value = "https://launches-url.com"

        fields = views.file_picker_to_form_fields_v11()

        LTIEvent.assert_called_once_with(
            request=pyramid_request,
            type=LTIEvent.Type.DEEP_LINKING,
            data={"document_url": _get_content_url_mock.return_value},
        )
        pyramid_request.registry.notify.has_call_with(LTIEvent.return_value)

        assert json.loads(fields["content_items"]) == {
            "@context": "http://purl.imsglobal.org/ctx/lti/v1/ContentItem",
            "@graph": [
                {
                    "@type": "LtiLinkItem",
                    "mediaType": "application/vnd.ims.lti.v1.ltilink",
                    "url": _get_content_url_mock.return_value,
                },
            ],
        }

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
    @pytest.mark.parametrize(
        "extra_params,extra_expected",
        [
            ({}, {}),
            ({"extra": "value", "none_value": None}, {"extra": "value"}),
        ],
    )
    def test_get_content_url(
        self, content, output_params, extra_params, extra_expected, pyramid_request
    ):
        pyramid_request.parsed_params.update(
            {"content": content, "extra_params": extra_params}
        )

        # pylint:disable=protected-access
        url = DeepLinkingFieldsViews._get_content_url(pyramid_request)

        output_params.update(extra_expected)
        assert url == Any.url.with_query(output_params)

    def test_it_with_unknown_file_type(self, pyramid_request):
        pyramid_request.parsed_params.update({"content": {"type": "other"}})

        with pytest.raises(ValueError):
            DeepLinkingFieldsViews(pyramid_request).file_picker_to_form_fields_v13()

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.parsed_params = {
            "deep_linking_settings": {"data": sentinel.deep_linking_settings_data},
            "content": {"type": "url", "url": "https://example.com"},
            "extra_params": {},
        }
        return pyramid_request

    @pytest.fixture
    def views(self, pyramid_request):
        return DeepLinkingFieldsViews(pyramid_request)

    @pytest.fixture
    def uuid(self, patch):
        return patch("lms.views.lti.deep_linking.uuid")

    @pytest.fixture
    def LTIEvent(self, patch):
        return patch("lms.views.lti.deep_linking.LTIEvent")

    @pytest.mark.usefixtures("db_session")
    @pytest.fixture
    def application_instance(self, application_instance):
        application_instance.lti_registration = factories.LTIRegistration()
        return application_instance

    @pytest.fixture
    def _get_content_url_mock(self, views):
        with patch.object(views, "_get_content_url", autospec=True) as patched:
            yield patched
