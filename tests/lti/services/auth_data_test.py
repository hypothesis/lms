# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import json
import mock
import pytest

from lti.models import OAuth2AccessToken
from lti.models import OAuth2Credentials
from lti.services.auth_data import AuthDataService


class TestAuthData(object):

    """Unit tests for the AuthData class."""

    def test_get_lti_token(self, auth_data):
        actual = auth_data.get_lti_token("93820000000000002")
        expected = "9382~IAbeGEFScV  ... IIMaEdK3dXlm2d9cjozd"
        assert actual == expected

    def test_get_lti_token_raises_KeyError_if_oauth_consumer_key_doesnt_exist(self, auth_data):
        with pytest.raises(KeyError) as ex:
            actual = auth_data.get_lti_token("KEY_DOES_NOT_EXIST")

    def test_get_lti_token_returns_None_if_theres_no_token_for_this_client_id(self,
                                                                              auth_data,
                                                                              db_session):
        db_session.add(OAuth2Credentials(
            client_id='OTHER_CLIENT_ID',
            client_secret='OTHER_SECRET',
            authorization_server='OTHER_SERVER',
        ))

        assert auth_data.get_lti_token('OTHER_CLIENT_ID') is None

    def test_get_lti_refresh_token(self, auth_data):
        actual = auth_data.get_lti_refresh_token("93820000000000002")
        expected = "9382~yRo ... Rlid9UXLhxfvwkWDnj"
        assert actual == expected

    def test_get_lti_refresh_token_raises_KeyError_if_oauth_consumer_key_doesnt_exist(self, auth_data):
        with pytest.raises(KeyError) as ex:
            actual = auth_data.get_lti_refresh_token("KEY_DOES_NOT_EXIST")

    def test_get_lti_refresh_token_returns_None_if_theres_no_token_for_this_client_id(self,
                                                                                     auth_data,
                                                                                     db_session):
        db_session.add(OAuth2Credentials(
            client_id='OTHER_CLIENT_ID',
            client_secret='OTHER_SECRET',
            authorization_server='OTHER_SERVER',
        ))

        assert auth_data.get_lti_refresh_token('OTHER_CLIENT_ID') is None

    def test_get_lti_secret(self,auth_data):
        actual = auth_data.get_lti_secret("93820000000000002")
        expected = "tJzcNSZadqlHTCW6ow  ... wodX3dfeuIokkLMjrQJqw3Y2"
        assert actual == expected

    def test_get_lti_secret_raises_KeyError_if_oauth_consumer_key_doesnt_exist(self, auth_data):
        with pytest.raises(KeyError) as ex:
            actual = auth_data.get_lti_secret("KEY_DOES_NOT_EXIST")

    def test_get_canvas_server(self,auth_data):
        actual = auth_data.get_canvas_server("93820000000000002")
        expected = "https://hypothesis.instructure.com:1000"
        assert actual == expected

    def test_get_canvas_server_raises_KeyError_if_oauth_consumer_key_doesnt_exist(self, auth_data):
        with pytest.raises(KeyError) as ex:
            actual = auth_data.get_canvas_server("KEY_DOES_NOT_EXIST")

    def test_set_tokens(self, auth_data):
        auth_data.set_tokens("93820000000000002", "new_lti_token", "new_refresh_token")
        assert auth_data.get_lti_token("93820000000000002") == "new_lti_token"
        assert auth_data.get_lti_refresh_token("93820000000000002") == "new_refresh_token"

    def test_set_tokens_deletes_existing_tokens_for_same_client_credentials(self,
                                                                            auth_data,
                                                                            db_session):
        # The current behaviour is that the database stores only one access
        # token per set of client credentials. set_tokens() replaces any
        # existing access tokens with the new ones.

        # Add multiple access tokens for the same credentials to the DB.
        # In practice this shouldn't happen, currently.
        db_session.add_all([
            OAuth2AccessToken(
                client_id='93820000000000002',
                access_token='access_token_1',
                refresh_token='refresh_token_1',
            ),
            OAuth2AccessToken(
                client_id='93820000000000002',
                access_token='access_token_2',
                refresh_token='refresh_token_2',
            ),
            OAuth2AccessToken(
                client_id='93820000000000002',
                access_token='access_token_3',
                refresh_token='refresh_token_3',
            ),
        ])

        # Set tokens should delete all existing access tokens for these client
        # credentials, and then add the new access token.
        auth_data.set_tokens("93820000000000002", "access_token_4", "refresh_token_4")

        # We expect the DB to contain only one access token whose values match
        # those we last passed to set_tokens().
        access_tokens = db_session.query(OAuth2AccessToken).all()
        assert len(access_tokens) == 1
        access_token = access_tokens[0]
        assert access_token.client_id == "93820000000000002"
        assert access_token.access_token == "access_token_4"
        assert access_token.refresh_token == "refresh_token_4"

    def test_set_tokens_doesnt_delete_tokens_for_other_client_credentials(self,
                                                                          auth_data,
                                                                          db_session):
        db_session.add(OAuth2Credentials(
            client_id='OTHER_CLIENT_ID',
            client_secret='OTHER_SECRET',
            authorization_server='OTHER_SERVER',
        ))
        auth_data.set_tokens("OTHER_CLIENT_ID", "OTHER_ACCESS_TOKEN", "OTHER_REFRESH_TOKEN")

        assert auth_data.get_lti_token("OTHER_CLIENT_ID") == "OTHER_ACCESS_TOKEN"
        assert auth_data.get_lti_token("93820000000000002") == (
            "9382~IAbeGEFScV  ... IIMaEdK3dXlm2d9cjozd")

    def test_set_tokens_throws_assertion_error_if_oauth_consumer_key_doesnt_exist(self, auth_data):
        with pytest.raises(AssertionError) as ex:
            actual = auth_data.set_tokens("KEY_DOES_NOT_EXIST", "new_lti_token", "new_refresh_token")


@pytest.fixture
def db_session(db_session):
    db_session.add_all([
        OAuth2Credentials(
            client_id='93820000000000002',
            client_secret='tJzcNSZadqlHTCW6ow  ... wodX3dfeuIokkLMjrQJqw3Y2',
            authorization_server='https://hypothesis.instructure.com:1000',
        ),
        OAuth2AccessToken(
            client_id='93820000000000002',
            access_token='9382~IAbeGEFScV  ... IIMaEdK3dXlm2d9cjozd',
            refresh_token='9382~yRo ... Rlid9UXLhxfvwkWDnj',
        ),
    ])
    return db_session


@pytest.fixture
def auth_data(db_session):
    return AuthDataService(db_session)
