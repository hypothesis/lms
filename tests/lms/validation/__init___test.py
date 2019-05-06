from unittest import mock

import marshmallow
import pytest
import webargs
from pyramid.interfaces import IViewDerivers

from lms.validation import _handle_error
from lms.validation import _validated_view
from lms.validation import includeme
from lms.validation import ValidationError


class TestHandleError:
    def test(self):
        webargs_exception = webargs.ValidationError(
            message={
                "field_name_1": ["Error message 1", "Error message 2"],
                "field_name_2": ["Error message 3"],
            }
        )

        # It wraps the webargs ValidationError in a custom ValidationError.
        with pytest.raises(ValidationError) as exc_info:
            _handle_error(
                webargs_exception,
                mock.sentinel.req,
                mock.sentinel.schema,
                mock.sentinel.status_code,
                mock.sentinel.headers,
            )

        # It exposes the webargs exception's messages as .messages.
        assert exc_info.value.messages == webargs_exception.messages

        # It raises the new exception from the original exception, so that the
        # original exception isn't lost.
        assert exc_info.value.__cause__ == webargs_exception


class TestValidatedView:
    def test_it_doesnt_wrap_views_that_dont_have_a_schema(self, info, view):
        # Pyramid calls every view deriver regardless of which view is being
        # derived.  It's up to the view deriver itself to not wrap views that
        # it isn't interested in. _validated_view() is only interested in views
        # that have a `schema=` argument in their view config.
        del info.options["schema"]

        assert _validated_view(view, info) == view

    def test_it_instantiates_the_views_schema(
        self, context, info, instantiate_schema, pyramid_request, view, schema
    ):
        # Derive and call the wrapper view.
        _validated_view(view, info)(context, pyramid_request)

        instantiate_schema.assert_called_once_with(schema, pyramid_request)

    def test_it_validates_the_request(
        self, context, info, parser, pyramid_request, view, instantiate_schema
    ):
        # Derive and call the wrapper view.
        _validated_view(view, info)(context, pyramid_request)

        # It uses the schema dict to parse the request.
        parser.parse.assert_called_once_with(
            instantiate_schema.return_value, pyramid_request
        )

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
        self, context, info, parser, pyramid_request, schema, view
    ):
        parser.parse.side_effect = ValidationError("error_messages")
        wrapper_view = _validated_view(view, info)

        with pytest.raises(ValidationError):
            wrapper_view(context, pyramid_request)

        view.assert_not_called()

    @pytest.fixture
    def context(self):
        """Return the Pyramid context object."""
        return mock.sentinel.context

    @pytest.fixture(autouse=True)
    def instantiate_schema(self, patch):
        return patch("lms.validation.instantiate_schema")

    @pytest.fixture
    def info(self):
        """Return the Pyramid view deriver info object.

        Pyramid passes one of these as an argument to every view deriver.
        """
        return mock.MagicMock(options={"schema": mock.sentinel.schema})

    @pytest.fixture()
    def parsed_params(self, parser):
        """Return the parsed params as returned by the webargs parser."""
        return parser.parse.return_value

    @pytest.fixture(autouse=True)
    def parser(self, patch):
        """Return the webargs parser object."""
        return patch("lms.validation.parser")

    @pytest.fixture
    def schema(self):
        """Return the view's configured schema object."""
        return mock.sentinel.schema

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
