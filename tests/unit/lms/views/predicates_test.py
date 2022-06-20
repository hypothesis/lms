from functools import partial
from unittest.mock import Mock, call, sentinel

import pytest
from h_matchers import Any

from lms.views.predicates import LTI_LAUNCH_PREDICATES, Predicate, includeme


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


@pytest.mark.parametrize("name,comparison", LTI_LAUNCH_PREDICATES.items())
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
