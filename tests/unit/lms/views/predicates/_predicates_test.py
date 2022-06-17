from unittest.mock import create_autospec, sentinel

import pytest

from lms.models import LTIParams
from lms.resources import LTILaunchResource
from lms.views.predicates._predicates import (
    ResourceLinkParam,
    get_db_configured_param,
    get_url_configured_param,
    is_authorized_to_configure_assignments,
    is_configured,
)


class TestGetURLConfiguredParam:
    @pytest.mark.parametrize(
        "params,expected",
        (
            ({}, None),
            ({"url": "any"}, "url"),
            ({"canvas_file": "any"}, "canvas_file"),
            ({"vitalsource_book": "any"}, "vitalsource_book"),
            ({"url": "any", "canvas_file": "any"}, "url"),
            ({"canvas_file": "any", "vitalsource_book": "any"}, "canvas_file"),
        ),
    )
    def test_it(self, pyramid_request, params, expected):
        pyramid_request.params = params

        assert get_url_configured_param(sentinel.context, pyramid_request) == expected


class TestGetDBConfiguredParam:
    @pytest.mark.parametrize(
        "lti_params,expected",
        (
            ({}, None),
            ({ResourceLinkParam.LTI: sentinel.link_id}, ResourceLinkParam.LTI),
            (
                {ResourceLinkParam.COPIED_BRIGHTSPACE: sentinel.link_id},
                ResourceLinkParam.COPIED_BRIGHTSPACE,
            ),
            (
                {ResourceLinkParam.COPIED_BLACKBOARD: sentinel.link_id},
                ResourceLinkParam.COPIED_BLACKBOARD,
            ),
        ),
    )
    def test_it(
        self, context, pyramid_request, assignment_service, lti_params, expected
    ):
        context.lti_params.update(lti_params)
        # Horrible work around
        if expected == ResourceLinkParam.LTI:
            context.resource_link_id = sentinel.link_id
        else:
            context.resource_link_id = None

        result = get_db_configured_param(context, pyramid_request)

        assert result == expected

        if expected:
            assignment_service.get_assignment.assert_called_once_with(
                tool_consumer_instance_guid=context.lti_params[
                    "tool_consumer_instance_guid"
                ],
                resource_link_id=sentinel.link_id,
            )

    def test_it_returns_none_if_assignment_is_not_found(
        self, context, pyramid_request, assignment_service
    ):
        context.resource_link_id = sentinel.link_id
        assignment_service.get_assignment.return_value = None

        assert not get_db_configured_param(context, pyramid_request)


class TestIsConfigured:
    PREDICATES = ["get_url_configured_param", "get_db_configured_param"]

    @pytest.mark.parametrize("predicate_name", PREDICATES)
    def test_it(self, predicates, predicate_name):
        pred_pos = self.PREDICATES.index(predicate_name)
        predicates[pred_pos].return_value = True

        result = is_configured(sentinel.context, sentinel.request)

        assert result

        for predicate in predicates[: pred_pos + 1]:
            predicate.assert_called_once_with(sentinel.context, sentinel.request)
        for predicate in predicates[pred_pos + 1 :]:
            predicate.assert_not_called()

    def test_it_returns_false_if_all_false(self):
        assert not is_configured(sentinel.context, sentinel.request)

    @pytest.fixture(autouse=True)
    def predicates(self, patch):
        predicates = []
        for predicate in self.PREDICATES:
            predicate = patch(f"lms.views.predicates._predicates.{predicate}")
            predicate.return_value = False
            predicates.append(predicate)

        return predicates


class TestIsAuthorizedToConfigureAssignments:
    @pytest.mark.parametrize(
        "roles,authorized",
        (
            ("administrator,noise", True),
            ("instructor,noise", True),
            ("INSTRUCTOR,noise", True),
            ("teachingassistant,noise", True),
            ("other", False),
        ),
    )
    def test_it(self, pyramid_request, roles, authorized):
        pyramid_request.lti_user = pyramid_request.lti_user._replace(roles=roles)

        result = is_authorized_to_configure_assignments(
            sentinel.context, pyramid_request
        )

        assert result == authorized

    def test_it_returns_false_with_no_user(self, pyramid_request):
        pyramid_request.lti_user = None

        assert not is_authorized_to_configure_assignments(
            sentinel.context, pyramid_request
        )


@pytest.fixture
def context():
    context = create_autospec(LTILaunchResource, spec_set=True, instance=True)
    context.lti_params = LTIParams({"tool_consumer_instance_guid": "guid"})
    return context
