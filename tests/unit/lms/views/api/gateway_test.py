import json
from unittest.mock import create_autospec, sentinel

import importlib_resources
import pytest
from h_matchers import Any
from jsonschema import Draft202012Validator
from pyramid.httpexceptions import HTTPForbidden

from lms.models import ReusedConsumerKey
from lms.resources import LTILaunchResource
from lms.views.api.gateway import _GatewayService, h_lti
from tests import factories


@pytest.mark.usefixtures("lti_h_service")
class TestHLTI:
    def test_it(self, context, pyramid_request, _GatewayService):
        response = h_lti(context, pyramid_request)

        _GatewayService.render_h_connection_info.assert_called_once_with(
            pyramid_request
        )
        _GatewayService.render_lti_context.assert_called_once_with(
            pyramid_request, context.course
        )
        assert response == {
            "api": {"h": _GatewayService.render_h_connection_info.return_value},
            "data": _GatewayService.render_lti_context.return_value,
        }

    def test_it_checks_for_guid_agreement(self, context, pyramid_request):
        context.application_instance.check_guid_aligns.side_effect = ReusedConsumerKey(
            "old", "new"
        )

        with pytest.raises(HTTPForbidden):
            h_lti(context, pyramid_request)

    def test_syncs_the_user_to_h(self, context, pyramid_request, lti_h_service):
        h_lti(context, pyramid_request)

        lti_h_service.sync.assert_called_once_with(
            [context.course], pyramid_request.lti_params
        )

    @pytest.fixture(autouse=True)
    def _GatewayService(self, patch):
        return patch("lms.views.api.gateway._GatewayService")


@pytest.mark.usefixtures("grouping_service")
class Test_GatewayService:
    def test_render_h_connection_info(self, pyramid_request, grant_token_service):
        connection_info = _GatewayService.render_h_connection_info(pyramid_request)

        grant_token_service.generate_token.assert_called_once_with(
            pyramid_request.lti_user.h_user
        )
        h_api_url = pyramid_request.registry.settings["h_api_url_public"]
        assert connection_info == {
            "list_endpoints": {
                "method": "GET",
                "url": h_api_url,
                "headers": {"Accept": "application/vnd.hypothesis.v2+json"},
            },
            "exchange_grant_token": {
                "method": "POST",
                "url": h_api_url + "token",
                "headers": {
                    "Accept": "application/vnd.hypothesis.v2+json",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                "data": {
                    "assertion": grant_token_service.generate_token.return_value,
                    "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                },
            },
        }

    def test_render_lti_context_renders_profile(self, pyramid_request, course):
        pyramid_request.lti_user = factories.LTIUser(
            user_id=sentinel.user_id, display_name=sentinel.display_name
        )

        data = _GatewayService.render_lti_context(pyramid_request, course)

        assert data["profile"] == {
            "display_name": sentinel.display_name,
            "lti": {"user_id": sentinel.user_id},
            "userid": Any.string.matching("^acct:.*@TEST_AUTHORITY$"),
        }

    def test_tender_lti_context_renders_groups(
        self, pyramid_request, course, grouping_service
    ):
        grouping = factories.BlackboardGroup(
            lms_name="grouping_lms_name",
            authority_provided_id="grouping_authority_provided_id",
            parent=course,
        )
        grouping_service.get_known_groupings.return_value = [course, grouping]

        data = _GatewayService.render_lti_context(pyramid_request, course)

        assert data["groups"] == [
            {
                "groupid": "group:course_authority_provided_id@TEST_AUTHORITY",
                "name": "course_lms_name",
                "lms": {
                    "id": course.lms_id,
                    "parentId": None,
                    "type": course.type,
                },
            },
            {
                "groupid": "group:grouping_authority_provided_id@TEST_AUTHORITY",
                "name": "grouping_lms_name",
                "lms": {
                    "id": grouping.lms_id,
                    "parentId": course.lms_id,
                    "type": grouping.type,
                },
            },
        ]

    @pytest.fixture
    def course(self):
        return factories.Course(
            lms_name="course_lms_name",
            authority_provided_id="course_authority_provided_id",
        )


@pytest.mark.usefixtures("grant_token_service", "lti_h_service", "grouping_service")
class TestHLTIConsumer:
    # These tests are "consumer tests" and ensure we meet the spec we have
    # provided to our users in our documentation

    def test_schema_is_valid(self, validator, schema):
        validator.check_schema(schema)

    def test_schema_examples_are_valid(self, validator, schema):
        for example in schema["examples"]:
            validator.validate(example)

    def test_gateway_output_matches_the_schema(
        self, validator, context, pyramid_request, grouping_service
    ):
        grouping_service.get_known_groupings.return_value = (
            factories.BlackboardGroup.create_batch(2) + [factories.Course()]
        )

        response = h_lti(context, pyramid_request)

        validator.validate(response)

    @pytest.fixture
    def schema(self):
        schema_file = importlib_resources.files("lms") / "../docs/gateway/schema.json"
        return json.loads(schema_file.read_text())

    @pytest.fixture
    def validator(self, schema):
        return Draft202012Validator(schema)


@pytest.fixture
def context():
    return create_autospec(LTILaunchResource, instance=True, spec_set=True)


@pytest.fixture
def pyramid_request(pyramid_request):
    pyramid_request.user = factories.User()
    pyramid_request.lti_params["tool_consumer_instance_guid"] = sentinel.guid

    return pyramid_request
