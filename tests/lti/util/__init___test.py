# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json
import urllib

import pytest

from lti.util import pack_state
from lti.util import unpack_state


class TestPackState(object):
    """Unit tests for pack_state()."""

    def test_it_returns_a_dict_as_a_url_quoted_json_string(self):
        data = {'foo': 'bar'}
        expected_string = '%7B%22foo%22%3A%20%22bar%22%7D'

        assert pack_state(data) == expected_string


class TestUnpackState(object):
    """Unit tests for unpack_state()."""

    def test_it_returns_a_url_quoted_json_string_as_a_dict(self):
        data = {
            'foo': 'FOO',
            'bar': 'BAR',
        }
        url_quoted_json_string = urllib.quote(json.dumps(data))

        returned = unpack_state(url_quoted_json_string)

        assert returned == data

    def test_it_raises_ValueError_if_the_string_isnt_valid_JSON(self):
        with pytest.raises(ValueError):
            unpack_state('THIS_IS_NOT_VALID_JSON')


class TestPackStateUnpackState(object):
    """Contract tests for how pack_state() and unpack_state() work together."""

    def test_unpack_state_reverses_pack_state(self):
        original_data = {'foo': 'bar'}

        url_quoted_json_string = pack_state(original_data)
        returned_data = unpack_state(url_quoted_json_string)

        assert returned_data == original_data
