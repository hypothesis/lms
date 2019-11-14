from unittest import mock

import pytest
from pyramid.interfaces import IViewDerivers

from lms.validation import ValidationError, _validated_view, includeme
from lms.validation._helpers import PyramidRequestSchema


class TestValidatedView:
    def test_it_doesnt_wrap_views_that_dont_have_a_schema(self, info, view):
        # Pyramid calls every view deriver regardless of which view is being
        # derived.  It's up to the view deriver itself to not wrap views that
        # it isn't interested in. _validated_view() is only interested in views
        # that have a `schema=` argument in their view config.
        del info.options["schema"]

        assert _validated_view(view, info) == view

    def test_it_instantiates_the_views_schema(
        self, context, info, pyramid_request, view, Schema
    ):
        # Derive and call the wrapper view.
        _validated_view(view, info)(context, pyramid_request)

        Schema.assert_called_once_with(pyramid_request)

    def test_it_validates_the_request(
        self, context, info, pyramid_request, view, Schema
    ):
        # Derive and call the wrapper view.
        _validated_view(view, info)(context, pyramid_request)

        # It uses the schema dict to parse the request.
        Schema.assert_called_once_with(pyramid_request)
        Schema.return_value.parse.assert_called_once_with()

    def test_it_adds_the_parsed_params_to_the_request(
        self, context, info, pyramid_request, view, parsed_params
    ):
        # Derive and call the wrapper view.
        _validated_view(view, info)(context, pyramid_request)

        assert pyramid_request.parsed_params == parsed_params

    def test_it_proxies_to_the_wrapped_view(self, context, info, pyramid_request, view):
        returned = _validated_view(view, info)(context, pyramid_request)

        view.assert_called_once_with(context, pyramid_request)
        assert returned == view.return_value

    def test_it_errors_if_validation_fails(
        self, context, info, Schema, pyramid_request, view
    ):
        Schema.return_value.parse.side_effect = ValidationError("error_messages")
        wrapper_view = _validated_view(view, info)

        with pytest.raises(ValidationError):
            wrapper_view(context, pyramid_request)

        view.assert_not_called()

    @pytest.fixture
    def context(self):
        """Return the Pyramid context object."""
        return mock.sentinel.context

    @pytest.fixture
    def info(self, Schema):
        """Return the Pyramid view deriver info object.

        Pyramid passes one of these as an argument to every view deriver.
        """
        return mock.MagicMock(options={"schema": Schema})

    @pytest.fixture()
    def parsed_params(self, Schema):
        """Return the parsed params as returned by the schema."""
        return Schema.return_value.parse.return_value

    @pytest.fixture
    def Schema(self):
        """Return the view's configured schema object."""
        return mock.create_autospec(PyramidRequestSchema, spec_set=True)

    @pytest.fixture
    def view(self):
        """Return the view that is being derived."""
        return mock.MagicMock()


class TestIncludeMe:
    def test_it_registers_the_view_deriver(self, pyramid_config, _validated_view):
        includeme(pyramid_config)

        assert _validated_view.options == ["schema"]
        assert (
            _validated_view
            in pyramid_config.registry.queryUtility(IViewDerivers).values()
        )

    @pytest.fixture(autouse=True)
    def _validated_view(self, patch):
        return patch("lms.validation._validated_view")
