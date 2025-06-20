import json
from datetime import datetime
from unittest.mock import create_autospec, patch, sentinel

import pytest
from freezegun import freeze_time
from h_matchers import Any
from pyramid.testing import DummyRequest

from lms.resources import LTILaunchResource
from lms.resources._js_config import JSConfig
from lms.validation import ValidationError
from lms.views.lti.deep_linking import (
    DeepLinkingFieldsRequestSchema,
    DeepLinkingFieldsViews,
    deep_linking_launch,
)
from tests import factories


@pytest.mark.usefixtures("user_service")
class TestDeepLinkingFieldsRequestSchema:
    @pytest.mark.parametrize(
        "payload",
        [
            {
                "content": {"type": "url", "url": "https://example.com"},
                "content_item_return_url": "return_url",
                "auto_grading_config": {
                    "grading_type": "scaled",
                    "activity_calculation": "separate",
                    "required_annotations": 10,
                    "required_replies": 2,
                },
                "extra_params": {},
            }
        ],
    )
    def test_valid_payloads(self, payload):
        request = DummyRequest(
            body=json.dumps(payload),
            headers={"Content-Type": "application/json; charset=UTF-8"},
        )
        request.content_type = request.headers["content-type"] = "application/json"

        DeepLinkingFieldsRequestSchema(request).parse()

    @pytest.mark.parametrize(
        "payload",
        [
            {
                "content": {"type": "url", "url": "https://example.com"},
                "content_item_return_url": "return_url",
                "auto_grading_config": {
                    "grading_type": "scaled",
                    "activity_calculation": "RANDOM",
                    "required_annotations": 10,
                    "required_replies": 2,
                },
                "extra_params": {},
            }
        ],
    )
    def test_invalid_payloads(self, payload):
        request = DummyRequest(
            body=json.dumps(payload),
            headers={"Content-Type": "application/json; charset=UTF-8"},
        )
        request.content_type = request.headers["content-type"] = "application/json"

        with pytest.raises(ValidationError):
            DeepLinkingFieldsRequestSchema(request).parse()


@pytest.mark.usefixtures("application_instance_service", "lti_h_service")
class TestDeepLinkingLaunch:
    def test_it(
        self,
        context,
        pyramid_request,
        lti_h_service,
        application_instance_service,
        course_service,
        misc_plugin,
        user_service,
    ):
        deep_linking_launch(context, pyramid_request)

        application_instance_service.update_from_lti_params.assert_called_once_with(
            pyramid_request.lti_user.application_instance, pyramid_request.lti_params
        )
        course_service.get_from_launch.assert_called_once_with(
            pyramid_request.product.family, pyramid_request.lti_params
        )
        user_service.upsert_lms_user.assert_called_once_with(
            pyramid_request.user, pyramid_request.lti_params
        )
        lti_h_service.sync.assert_called_once_with(
            [course_service.get_from_launch.return_value], pyramid_request.params
        )
        context.js_config.enable_file_picker_mode.assert_called_once_with(
            form_action="TEST_CONTENT_ITEM_RETURN_URL",
            form_fields={
                "lti_message_type": "ContentItemSelection",
                "lti_version": "TEST_LTI_VERSION",
            },
            course=course_service.get_from_launch.return_value,
            prompt_for_title=misc_plugin.deep_linking_prompt_for_title,
            prompt_for_gradable=misc_plugin.deep_linking_prompt_for_gradable.return_value,
        )
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
        context = create_autospec(LTILaunchResource, spec_set=True, instance=True)
        context.js_config = create_autospec(JSConfig, spec_set=True, instance=True)
        return context


@pytest.mark.usefixtures("application_instance_service", "misc_plugin")
class TestDeepLinkingFieldsView:
    @freeze_time("2022-04-04")
    @pytest.mark.parametrize("title", [None, "title"])
    @pytest.mark.parametrize("gradable_max_points", [None, 10])
    def test_it_for_v13(
        self,
        jwt_service,
        application_instance,
        views,
        uuid,
        LTIEvent,
        pyramid_request,
        misc_plugin,
        _get_assignment_configuration,  # noqa: PT019
        title,
        gradable_max_points,
    ):
        _get_assignment_configuration.return_value = {}
        if title:
            _get_assignment_configuration.return_value["title"] = title
        if gradable_max_points:
            _get_assignment_configuration.return_value["gradable_max_points"] = (
                gradable_max_points
            )

        fields = views.file_picker_to_form_fields_v13()

        message = {
            "exp": datetime(2022, 4, 4, 1, 0),  # noqa: DTZ001
            "iat": datetime(2022, 4, 4, 0, 0),  # noqa: DTZ001
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
                    "url": misc_plugin.get_deeplinking_launch_url.return_value,
                    "custom": _get_assignment_configuration.return_value,
                }
            ],
            "https://purl.imsglobal.org/spec/lti-dl/claim/data": sentinel.deep_linking_settings_data,
        }
        if title:
            message["https://purl.imsglobal.org/spec/lti-dl/claim/content_items"][0][
                "title"
            ] = title

        if gradable_max_points:
            message["https://purl.imsglobal.org/spec/lti-dl/claim/content_items"][0][
                "lineItem"
            ] = {"scoreMaximum": gradable_max_points}

        jwt_service.encode_with_private_key.assert_called_once_with(message)
        LTIEvent.from_request.assert_called_once_with(
            request=pyramid_request,
            type_=LTIEvent.Type.DEEP_LINKING,
            data=_get_assignment_configuration.return_value,
        )
        pyramid_request.registry.notify.has_call_with(
            LTIEvent.from_request.return_value
        )
        assert fields["JWT"] == jwt_service.encode_with_private_key.return_value

    @pytest.mark.usefixtures("LTIEvent")
    @pytest.mark.parametrize("settings", [None, {}, {"data": None}])
    def test_it_for_v13_missing_deep_linking_settings_data(
        self, jwt_service, views, pyramid_request, settings
    ):
        pyramid_request.parsed_params["opaque_data_lti13"] = settings

        views.file_picker_to_form_fields_v13()

        jwt_service.encode_with_private_key.assert_called_once_with(
            message := Any.dict()
        )
        assert (
            "https://purl.imsglobal.org/spec/lti-dl/claim/data "
            not in message.last_matched()  # pylint: disable=unsupported-membership-test
        )

    @pytest.mark.parametrize("title", [None, "title"])
    @pytest.mark.parametrize("opaque_data_lti11", [None, "DATA"])
    def test_it_for_v11(
        self,
        views,
        _get_assignment_configuration,  # noqa: PT019
        pyramid_request,
        LTIEvent,
        misc_plugin,
        title,
        opaque_data_lti11,
        oauth1_service,
        application_instance,
    ):
        misc_plugin.get_deeplinking_launch_url.return_value = "LAUNCH_URL"
        pyramid_request.parsed_params["opaque_data_lti11"] = opaque_data_lti11

        if title:
            _get_assignment_configuration.return_value = {"title": title}

        fields = views.file_picker_to_form_fields_v11()

        LTIEvent.from_request.assert_called_once_with(
            request=pyramid_request,
            type_=LTIEvent.Type.DEEP_LINKING,
            data=_get_assignment_configuration.return_value,
        )
        pyramid_request.registry.notify.has_call_with(
            LTIEvent.from_request.return_value
        )

        content_items = {
            "@context": "http://purl.imsglobal.org/ctx/lti/v1/ContentItem",
            "@graph": [
                {
                    "@type": "LtiLinkItem",
                    "mediaType": "application/vnd.ims.lti.v1.ltilink",
                    "url": "LAUNCH_URL",
                    "custom": _get_assignment_configuration.return_value,
                },
            ],
        }

        if title:
            content_items["@graph"][0]["title"] = title

        expected_fields = {
            "lti_message_type": "ContentItemSelection",
            "lti_version": "LTI-1p0",
            "content_items": json.dumps(content_items),
        }

        if opaque_data_lti11:
            expected_fields["data"] = opaque_data_lti11

        oauth1_service.sign.assert_called_once_with(
            application_instance, sentinel.return_url, "post", expected_fields
        )
        assert fields == oauth1_service.sign.return_value

    @pytest.mark.parametrize(
        "content,expected_from_content",
        [
            (
                {"type": "url", "url": "https://example.com"},
                {"url": "https://example.com"},
            ),
        ],
    )
    @pytest.mark.parametrize(
        "data,expected",
        [
            ({}, {}),
            ({"title": "title"}, {"title": "title"}),
            ({"assignment_gradable_max_points": 1}, {"gradable_max_points": 1}),
            ({"group_set": "1"}, {"group_set": "1"}),
            (
                {"group_set": "1", "title": "title"},
                {"group_set": "1", "title": "title"},
            ),
            (
                {"auto_grading_config": {"key": "value"}},
                {"auto_grading_config": '{"key": "value"}'},
            ),
        ],
    )
    def test__get_assignment_configuration(
        self, content, expected_from_content, pyramid_request, data, expected, uuid
    ):
        pyramid_request.parsed_params.update({"content": content, **data})

        config = DeepLinkingFieldsViews._get_assignment_configuration(pyramid_request)  # noqa: SLF001

        assert config == {
            "deep_linking_uuid": uuid.uuid4().hex,
            **expected,
            **expected_from_content,
        }

    def test_it_with_unknown_file_type(self, pyramid_request):
        pyramid_request.parsed_params.update({"content": {"type": "other"}})

        with pytest.raises(ValueError):  # noqa: PT011
            DeepLinkingFieldsViews(pyramid_request).file_picker_to_form_fields_v13()

    @pytest.fixture
    def pyramid_request(self, pyramid_request):
        pyramid_request.parsed_params = {
            "opaque_data_lti13": {"data": sentinel.deep_linking_settings_data},
            "content": {"type": "url", "url": "https://example.com"},
            "content_item_return_url": sentinel.return_url,
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

    @pytest.fixture
    def application_instance(self, application_instance):
        application_instance.lti_registration = factories.LTIRegistration()
        return application_instance

    @pytest.fixture
    def _get_assignment_configuration(self, views):
        with patch.object(
            views, "_get_assignment_configuration", autospec=True
        ) as patched:
            patched.return_value = {}
            yield patched
