# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from lti.models import OAuth2UnvalidatedCredentials


class TestOAuthUnvalidated2Credentials(object):

    def test_it_persists_the_fields(self, db_session):
        db_session.add(OAuth2UnvalidatedCredentials(client_id="TEST_ID",
                                                    client_secret="TEST_SECRET",
                                                    authorization_server="TEST_AUTH_SERVER",
                                                    email_address="TEST_EMAIL",
        ))

        persisted = (db_session.query(OAuth2UnvalidatedCredentials)
                               .filter_by(client_id="TEST_ID").one())
        assert persisted.client_id == "TEST_ID"
        assert persisted.client_secret == "TEST_SECRET"
        assert persisted.authorization_server == "TEST_AUTH_SERVER"
        assert persisted.email_address == "TEST_EMAIL"

    def test_you_can_add_multiple_rows_with_the_same_values(self, db_session):
        db_session.add_all([
            OAuth2UnvalidatedCredentials(client_id="TEST_ID",
                                         client_secret="TEST_SECRET",
                                         authorization_server="TEST_AUTH_SERVER",
                                         email_address="TEST_EMAIL",
            ),
            OAuth2UnvalidatedCredentials(client_id="TEST_ID",
                                         client_secret="TEST_SECRET",
                                         authorization_server="TEST_AUTH_SERVER",
                                         email_address="TEST_EMAIL",
            ),
            OAuth2UnvalidatedCredentials(client_id="TEST_ID",
                                         client_secret="TEST_SECRET",
                                         authorization_server="TEST_AUTH_SERVER",
                                         email_address="TEST_EMAIL",
            ),
        ])

        db_session.flush()
