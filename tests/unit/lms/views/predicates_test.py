from functools import partial
from unittest.mock import Mock, call, sentinel

import pytest
from h_matchers import Any

from lms.views.lti.basic_launch import (
    authorized_to_configure_assignments,
    has_document_url,
)
from lms.views.predicates import Predicate, includeme


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

    def test_register(self, config):
        def is_an_example(_config, _request):
            """Pretend to be a predicate comparison function."""

        Predicate.register(config, is_an_example)

        predicate_partial = Any.object.of_type(partial).with_attrs(
            {
                "func": Predicate,
                "keywords": {"name": "is_an_example", "comparison": is_an_example},
            }
        )
        config.add_view_predicate.assert_has_calls(
            [call(name="is_an_example", factory=predicate_partial)]
        )

    @pytest.fixture
    def config(self):
        return Mock(spec_set=["add_view_predicate"])

    @pytest.fixture
    def predicate(self):
        return Predicate(
            value=sentinel.value, info=sentinel.info, name="name", comparison=Mock()
        )


class TestIncludeme:
    def test_it(self, Predicate):
        includeme(sentinel.config)

        Predicate.register.assert_has_calls(
            [
                call(sentinel.config, has_document_url),
                call(sentinel.config, authorized_to_configure_assignments),
            ]
        )

    @pytest.fixture
    def Predicate(self, patch):
        return patch("lms.views.predicates.Predicate")
