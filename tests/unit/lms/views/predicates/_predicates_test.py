from unittest.mock import create_autospec, sentinel

import pytest

from lms.models import LTIParams
from lms.resources import LTILaunchResource
from lms.views.predicates._predicates import (
    ResourceLinkParam,
    is_authorized_to_configure_assignments,
    is_blackboard_copied,
    is_brightspace_copied,
    is_canvas_file,
    is_configured,
    is_db_configured,
    is_deep_linking_configured,
    is_vitalsource_book,
)


class TestIsCanvasFile:
    @pytest.mark.parametrize(
        "params,expected", (({}, False), ({"canvas_file": "any"}, True))
    )
    def test_it(self, pyramid_request, params, expected):
        pyramid_request.params = params

        assert is_canvas_file(sentinel.context, pyramid_request) == expected


class TestIsVitalsourceBook:
    @pytest.mark.parametrize(
        "params,expected", (({}, False), ({"vitalsource_book": "any"}, True))
    )
    def test_it(self, pyramid_request, params, expected):
        pyramid_request.params = params

        assert is_vitalsource_book(sentinel.context, pyramid_request) == expected


class TestIsDeepLinkingConfigured:
    @pytest.mark.parametrize("params,expected", (({}, False), ({"url": "any"}, True)))
    def test_it(self, pyramid_request, params, expected):
        pyramid_request.params = params

        assert is_deep_linking_configured(sentinel.context, pyramid_request) == expected


class TestIsDBConfigured:
    @pytest.mark.parametrize("exists", (True, False))
    def test_it(self, context, pyramid_request, assignment_service, exists):
        assignment_service.assignment_exists.return_value = exists

        result = is_db_configured(context, pyramid_request)

        assert result == exists
        assignment_service.assignment_exists.assert_called_once_with(
            tool_consumer_instance_guid=context.lti_params[
                "tool_consumer_instance_guid"
            ],
            resource_link_id=context.resource_link_id,
        )


class TestCourseCopied:
    def test_it(
        self,
        context,
        pyramid_request,
        is_db_configured,
        comparison,
        param,
        assignment_service,
    ):
        pyramid_request.params[param] = sentinel.link_id

        result = comparison(context, pyramid_request)

        assert result
        is_db_configured.assert_called_once_with(context, pyramid_request)
        assignment_service.assignment_exists.assert_called_once_with(
            tool_consumer_instance_guid=context.lti_params[
                "tool_consumer_instance_guid"
            ],
            resource_link_id=sentinel.link_id,
        )

    def test_it_returns_false_for_db_configured_launches(
        self, context, pyramid_request, is_db_configured, comparison
    ):
        is_db_configured.return_value = True

        assert not comparison(context, pyramid_request)

    def test_it_returns_false_for_no_db_record(
        self, context, pyramid_request, comparison, assignment_service
    ):
        assignment_service.assignment_exists.return_value = False

        assert not comparison(context, pyramid_request)

    @pytest.fixture(params=[is_brightspace_copied, is_blackboard_copied])
    def comparison(self, request):
        return request.param

    @pytest.fixture
    def param(self, comparison):
        return {
            is_brightspace_copied: ResourceLinkParam.COPIED_BRIGHTSPACE,
            is_blackboard_copied: ResourceLinkParam.COPIED_BLACKBOARD,
        }[comparison]

    @pytest.fixture(autouse=True)
    def is_db_configured(self, patch):
        is_db_configured = patch("lms.views.predicates._predicates.is_db_configured")
        is_db_configured.return_value = False
        return is_db_configured


class TestIsConfigured:
    PREDICATES = [
        "is_canvas_file",
        "is_deep_linking_configured",
        "is_vitalsource_book",
        "is_db_configured",
        "is_blackboard_copied",
        "is_brightspace_copied",
    ]

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
