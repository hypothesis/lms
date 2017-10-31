from sqlalchemy.exc import IntegrityError
import pytest

from lti.models import ApplicationInstance


class TestApplicationInstance(object):
  def test_test(self):
    assert True
#    def test_it_persists_the_client_id_access_token_and_refresh_token(self,
#                                                                      db_session,
#                                                                      oauth2_credentials):
#        db_session.add(OAuth2AccessToken(credentials=oauth2_credentials,
#                                         access_token="TEST_ACCESS_TOKEN",
#                                         refresh_token="TEST_REFRESH_TOKEN"))
#
#        persisted = db_session.query(OAuth2AccessToken).one()
#        assert persisted.client_id == oauth2_credentials.client_id
#        assert persisted.access_token == "TEST_ACCESS_TOKEN"
#        assert persisted.refresh_token == "TEST_REFRESH_TOKEN"
#

