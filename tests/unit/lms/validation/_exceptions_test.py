from unittest import mock
from urllib.parse import parse_qs, urlparse

import pytest
from h_matchers import Any
from pyramid.httpexceptions import HTTPFound

from lms.validation import LTIToolRedirect, ValidationError


class TestValidationError:
    def test(self):
        validation_error = ValidationError(mock.sentinel.messages)

        assert validation_error.messages == mock.sentinel.messages
        assert validation_error.status_code == 422


class TestLTIToolRedirect:
    def test_it_is_a_redirect(self, redirect):
        assert redirect == Any.instance_of(HTTPFound)
        assert redirect.status_int == 302

    def test_it_appends_lti_parameter(self, redirect):
        url = urlparse(redirect.location)
        params = parse_qs(url.query)

        assert url._replace(query=None).geturl() == "http://example.com"
        assert params == Any.dict.containing(
            {"a": ["1"], "lti_msg": [Any.string.matching(".*field_name.*error_name.*")]}
        )

    def test_we_produce_a_string_message(self, redirect):
        assert redirect.detail == Any.string.matching(".*field_name.*error_name.*")

    @pytest.mark.parametrize(
        "messages",
        [
            pytest.param("a string", id="string"),
            pytest.param([], id="list"),
            pytest.param({"a": "b"}, id="dict of string"),
        ],
    )
    def test_it_requires_well_formatted_messages(self, messages):
        with pytest.raises(ValueError):
            LTIToolRedirect("http://example.com", messages)

    @pytest.fixture
    def redirect(self):
        return LTIToolRedirect("http://example.com?a=1", {"field_name": ["error_name"]})
