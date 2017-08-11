# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json
import mock
import pytest

from lti.services.auth_data import AuthDataService


class TestAuthData(object):

    """Unit tests for the AuthData class."""

    def test_it_loads_json_from_file(self, auth_data):
        assert auth_data.get_lti_token("93820000000000002") == "9382~IAbeGEFScV  ... IIMaEdK3dXlm2d9cjozd"
        assert auth_data.get_lti_refresh_token("93820000000000002") == "9382~yRo ... Rlid9UXLhxfvwkWDnj"
        assert auth_data.get_lti_secret("93820000000000002") == "tJzcNSZadqlHTCW6ow  ... wodX3dfeuIokkLMjrQJqw3Y2"
        assert auth_data.get_canvas_server("93820000000000002") == "https://hypothesis.instructure.com:1000"

    def test_get_lti_token(self, auth_data):
        actual = auth_data.get_lti_token("93820000000000002")
        expected = "9382~IAbeGEFScV  ... IIMaEdK3dXlm2d9cjozd"
        assert actual == expected

    def test_get_lti_token_throws_key_error_if_oauth_consumer_key_doesnt_exist(self, auth_data):
        with pytest.raises(KeyError) as ex:
            actual = auth_data.get_lti_token("KEY_DOES_NOT_EXIST")

    def test_get_lti_refresh_token(self, auth_data):
        actual = auth_data.get_lti_refresh_token("93820000000000002")
        expected = "9382~yRo ... Rlid9UXLhxfvwkWDnj"
        assert actual == expected

    def test_get_lti_refresh_token_throws_key_error_if_oauth_consumer_key_doesnt_exist(self, auth_data):
        with pytest.raises(KeyError) as ex:
            actual = auth_data.get_lti_refresh_token("KEY_DOES_NOT_EXIST")

    def test_get_lti_secret(self,auth_data):
        actual = auth_data.get_lti_secret("93820000000000002")
        expected = "tJzcNSZadqlHTCW6ow  ... wodX3dfeuIokkLMjrQJqw3Y2"
        assert actual == expected

    def test_get_lti_secret_throws_key_error_if_oauth_consumer_key_doesnt_exist(self, auth_data):
        with pytest.raises(KeyError) as ex:
            actual = auth_data.get_lti_secret("KEY_DOES_NOT_EXIST")

    def test_get_canvas_server_without_port(self,auth_data):
        auth_data.auth_data["93820000000000002"]["canvas_server_port"] = None

        actual = auth_data.get_canvas_server("93820000000000002")
        expected = "https://hypothesis.instructure.com"
        assert actual == expected

    def test_get_canvas_server_with_port(self,auth_data):
        actual = auth_data.get_canvas_server("93820000000000002")
        expected = "https://hypothesis.instructure.com:1000"
        assert actual == expected

    def test_get_canvas_server_throws_key_error_if_oauth_consumer_key_doesnt_exist(self, auth_data):
        with pytest.raises(KeyError) as ex:
            actual = auth_data.get_canvas_server("KEY_DOES_NOT_EXIST")

    def test_set_tokens(self, auth_data, open_):
        open_.reset_mock()

        auth_data.set_tokens("93820000000000002", "new_lti_token", "new_refresh_token")
        assert auth_data.get_lti_token("93820000000000002") == "new_lti_token"
        assert auth_data.get_lti_refresh_token("93820000000000002") == "new_refresh_token"
        open_.assert_called_once_with(auth_data._name, 'wb')
        j = json.dumps(auth_data.auth_data, indent=2, sort_keys=True)
        open_.return_value.write.assert_called_once_with(j)
        open_.return_value.close.assert_called_once_with()

    def test_set_tokens_throws_assertion_error_if_oauth_consumer_key_doesnt_exist(self, auth_data):
        with pytest.raises(AssertionError) as ex:
            actual = auth_data.set_tokens("KEY_DOES_NOT_EXIST", "new_lti_token", "new_refresh_token")


@pytest.fixture
def open_():
    open_ = mock.MagicMock()
    open_.return_value.read.return_value = '''{
        "93820000000000002": {
            "canvas_server_host": "hypothesis.instructure.com",
            "canvas_server_port": "1000",
            "canvas_server_scheme": "https",
            "lti_refresh_token": "9382~yRo ... Rlid9UXLhxfvwkWDnj",
            "lti_token": "9382~IAbeGEFScV  ... IIMaEdK3dXlm2d9cjozd",
            "secret": "tJzcNSZadqlHTCW6ow  ... wodX3dfeuIokkLMjrQJqw3Y2"
        }
    }'''
    return open_


@pytest.fixture
def auth_data(open_):
    return AuthDataService(open_)
