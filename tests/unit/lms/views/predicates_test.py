from functools import partial
from unittest.mock import Mock, call, sentinel

import pytest
from h_matchers import Any

from lms.views.predicates import (
    PREDICATES,
    Predicate,
    has_document_url,
    includeme,
    is_authorized_to_configure_assignments,
)


class TestHasDocumentURL:
    @pytest.mark.parametrize("document_url", (None, "a_url"))
    def test_it(self, document_url_service, pyramid_request, document_url):
        document_url_service.get_document_url.return_value = document_url

        result = has_document_url(sentinel.context, pyramid_request)

        document_url_service.get_document_url.assert_called_once_with(
            sentinel.context, pyramid_request
        )
        assert result == bool(document_url)


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


class TestPredicate:
    def test_text(self, predicate):
        assert predicate.text() == "name = sentinel.value"

    def test_phash(self, predicate):
        assert predicate.phash() == "name = sentinel.value"

    @pytest.mark.parametrize("value", (True, False))
    @pytest.mark.parametrize("comparison_return", (True, False))
    def test__call__(self, predicate, value, comparison_return):
        predicate.value = value
        predicate.comparison.return_value = comparison_return

        result = predicate(sentinel.context, sentinel.request)

        predicate.comparison.assert_called_once_with(sentinel.context, sentinel.request)
        assert result == (value == comparison_return)

    def test__call__matches_None_with_False(self, predicate):
        predicate.value = False
        predicate.comparison.return_value = None

        assert predicate(sentinel.context, sentinel.request)

    @pytest.fixture
    def predicate(self):
        return Predicate(
            value=sentinel.value, info=sentinel.info, name="name", comparison=Mock()
        )


@pytest.mark.parametrize("name,comparison", PREDICATES.items())
def test_includeme(name, comparison):
    config = Mock(spec_set=["add_view_predicate"])

    includeme(config)

    predicate_partial = Any.object.of_type(partial).with_attrs(
        {
            "func": Predicate,
            "keywords": {"name": name, "comparison": comparison},
        }
    )
    config.add_view_predicate.assert_has_calls(
        [call(name=name, factory=predicate_partial)]
    )
