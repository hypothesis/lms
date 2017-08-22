# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from sqlalchemy.exc import IntegrityError
import pytest

from lti.models import OAuth2AccessToken


class TestOAuth2AccessToken(object):

    def test_it_persists_the_client_id_access_token_and_refresh_token(self,
                                                                      db_session,
                                                                      oauth2_credentials):
        db_session.add(OAuth2AccessToken(credentials=oauth2_credentials,
                                         access_token="TEST_ACCESS_TOKEN",
                                         refresh_token="TEST_REFRESH_TOKEN"))

        persisted = db_session.query(OAuth2AccessToken).one()
        assert persisted.client_id == oauth2_credentials.client_id
        assert persisted.access_token == "TEST_ACCESS_TOKEN"
        assert persisted.refresh_token == "TEST_REFRESH_TOKEN"

    def test_the_OAuth2Credentials_is_accessible_as_the_credentials_property(self,
                                                                             oauth2_credentials):
        access_token = OAuth2AccessToken(credentials=oauth2_credentials,
                                         access_token="TEST_ACCESS_TOKEN",
                                         refresh_token="TEST_REFRESH_TOKEN")

        assert access_token.credentials == oauth2_credentials

    def test_the_client_id_is_accessible_as_the_client_id_property(self,
                                                                   oauth2_credentials,
                                                                   db_session):
        access_token = OAuth2AccessToken(credentials=oauth2_credentials,
                                         access_token="TEST_ACCESS_TOKEN",
                                         refresh_token="TEST_REFRESH_TOKEN")
        db_session.add(access_token)
        db_session.flush()

        assert access_token.client_id == oauth2_credentials.client_id

    def test_unique_ids_are_automatically_generated(self, db_session, oauth2_credentials):
        access_token = OAuth2AccessToken(credentials=oauth2_credentials,
                                         access_token="TEST_ACCESS_TOKEN",
                                         refresh_token="TEST_REFRESH_TOKEN")
        db_session.add(access_token)
        db_session.flush()  # The id is generated when the session is flushed.

        assert access_token.id

    def test_client_id_must_refer_to_an_existing_client_id(self, db_session):
        db_session.add(OAuth2AccessToken(client_id="DOES_NOT_EXIST",
                                         access_token="TEST_ACCESS_TOKEN",
                                         refresh_token="TEST_REFRESH_TOKEN"))

        with pytest.raises(IntegrityError):
            db_session.flush()

    def test_client_id_cant_be_None(self, db_session):
        db_session.add(OAuth2AccessToken(client_id=None,
                                         access_token="TEST_ACCESS_TOKEN",
                                         refresh_token="TEST_REFRESH_TOKEN"))

        expected_message = 'null value in column "client_id" violates not-null constraint'
        with pytest.raises(IntegrityError, match=expected_message):
            db_session.flush()

    def test_a_single_OAuth2Credentials_can_have_multiple_OAuth2AccessTokens(self,
                                                                             db_session,
                                                                             oauth2_credentials):
        db_session.add_all([
            OAuth2AccessToken(credentials=oauth2_credentials,
                              access_token="FIRST_ACCESS_TOKEN",
                              refresh_token="FIRST_REFRESH_TOKEN"),
            OAuth2AccessToken(credentials=oauth2_credentials,
                              access_token="SECOND_ACCESS_TOKEN",
                              refresh_token="SECOND_REFRESH_TOKEN"),
        ])
        db_session.commit()

    def test_access_token_cant_be_None(self, db_session, oauth2_credentials):
        db_session.add(OAuth2AccessToken(credentials=oauth2_credentials,
                                         access_token=None,
                                         refresh_token="TEST_REFRESH_TOKEN"))

        expected_message = 'null value in column "access_token" violates not-null constraint'
        with pytest.raises(IntegrityError, match=expected_message):
            db_session.flush()

    def test_refresh_token_can_be_None(self, db_session, oauth2_credentials):
        db_session.add(OAuth2AccessToken(credentials=oauth2_credentials,
                                         access_token="TEST_ACCESS_TOKEN",
                                         refresh_token=None))
        db_session.flush()

    @pytest.fixture
    def oauth2_credentials(self, factories):
        return factories.OAuth2Credentials()
