import json
from unittest.mock import create_autospec, sentinel

import importlib_resources
import pytest
from jsonschema import Draft202012Validator
from pyramid.httpexceptions import HTTPForbidden

from lms.models import Grouping, ReusedConsumerKey
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
        _GatewayService.render_lti_context.assert_called_once_with(pyramid_request)
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


@pytest.mark.usefixtures("assignment_service", "course_service", "grant_token_service")
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

    def test_render_lti_context_for_course(
        self, pyramid_request, assignment_service, course_service, assignment
    ):
        pyramid_request.lti_params.pop("resource_link_id", None)
        pyramid_request.lti_params["context_id"] = sentinel.context_id
        assignment_service.get_assignments_for_grouping.return_value = [assignment]

        result = _GatewayService.render_lti_context(pyramid_request)

        course_service.get_by_context_id.assert_called_once_with(sentinel.context_id)
        assignment_service.get_assignments_for_grouping.assert_called_once_with(
            course_service.get_by_context_id.return_value.id, eager_load=True
        )

        self.assert_render_lti_context_correct(result)

    def test_render_lti_context_with_no_course(self, pyramid_request, course_service):
        pyramid_request.lti_params.pop("resource_link_id", None)
        pyramid_request.lti_params["context_id"] = sentinel.context_id
        course_service.get_by_context_id.return_value = None

        assert _GatewayService.render_lti_context(pyramid_request) == {
            "assignments": []
        }

    def test_render_lti_context_for_assignment(
        self, pyramid_request, assignment_service, assignment
    ):
        pyramid_request.lti_params[
            "tool_consumer_instance_guid"
        ] = sentinel.tool_consumer_instance_guid
        pyramid_request.lti_params["resource_link_id"] = sentinel.resource_link_id
        assignment_service.get_assignment.return_value = assignment

        result = _GatewayService.render_lti_context(pyramid_request)

        assignment_service.get_assignment.assert_called_once_with(
            tool_consumer_instance_guid=sentinel.tool_consumer_instance_guid,
            resource_link_id=sentinel.resource_link_id,
            eager_load=True,
        )
        self.assert_render_lti_context_correct(result)

    def test_render_lti_context_with_no_assigment(
        self, pyramid_request, assignment_service
    ):
        pyramid_request.lti_params[
            "tool_consumer_instance_guid"
        ] = sentinel.tool_consumer_instance_guid
        pyramid_request.lti_params["resource_link_id"] = sentinel.resource_link_id
        assignment_service.get_assignment.return_value = None

        assert _GatewayService.render_lti_context(pyramid_request) == {
            "assignments": []
        }

    def assert_render_lti_context_correct(self, result):
        assert result == {
            "assignments": [
                {
                    "lms": {"document_url": "document_url"},
                    "lti": {
                        "resource_link_description": "description",
                        "resource_link_id": "resource_link_id",
                        "resource_link_title": "title",
                    },
                    "groups": [
                        {
                            "groupid": "group:s1_id@TEST_AUTHORITY",
                            "lms": {
                                "id": "s1_lms_id",
                                "parentId": "c_lms_id",
                                "type": Grouping.Type.CANVAS_SECTION,
                            },
                            "name": "section_name_1",
                        },
                        {
                            "groupid": "group:s2_id@TEST_AUTHORITY",
                            "lms": {
                                "id": "s2_lms_id",
                                "parentId": "c_lms_id",
                                "type": Grouping.Type.CANVAS_SECTION,
                            },
                            "name": "section_name_2",
                        },
                        {
                            "groupid": "group:c_id@TEST_AUTHORITY",
                            "lms": {
                                "id": "c_lms_id",
                                "parentId": None,
                                "type": Grouping.Type.COURSE,
                            },
                            "name": "course_name",
                        },
                    ],
                }
            ]
        }


@pytest.mark.usefixtures(
    "grant_token_service", "lti_h_service", "assignment_service", "course_service"
)
class TestHLTIConsumer:
    # These tests are "consumer tests" and ensure we meet the spec we have
    # provided to our users in our documentation

    def test_schema_is_valid(self, validator, schema):
        validator.check_schema(schema)

    def test_schema_examples_are_valid(self, validator, schema):
        for example in schema["examples"]:
            validator.validate(example)

    def test_gateway_output_matches_the_schema(
        self, validator, context, pyramid_request, assignment_service, assignment
    ):
        # Flip into course mode and provide some content to format
        pyramid_request.lti_params["context_id"] = sentinel.context_id
        assignment_service.get_assignments_for_grouping.return_value = [assignment]

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
def assignment():
    # Use baked values, so we can have static comparisons in the tests

    course = factories.Course(
        lms_name="course_name", authority_provided_id="c_id", lms_id="c_lms_id"
    )
    groups = [
        factories.CanvasSection(
            lms_name="section_name_1", authority_provided_id="s1_id", lms_id="s1_lms_id"
        ),
        factories.CanvasSection(
            lms_name="section_name_2", authority_provided_id="s2_id", lms_id="s2_lms_id"
        ),
    ]
    course.children = groups
    for group in groups:
        group.parent = course

    assignment = factories.Assignment.create(
        document_url="document_url",
        resource_link_id="resource_link_id",
        title="title",
        description="description",
    )

    assignment.groupings = list(groups) + [course]

    return assignment


@pytest.fixture
def context():
    return create_autospec(LTILaunchResource, instance=True, spec_set=True)


@pytest.fixture
def pyramid_request(pyramid_request):
    pyramid_request.lti_params["tool_consumer_instance_guid"] = sentinel.guid

    return pyramid_request
