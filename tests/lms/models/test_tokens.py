from lms.models.tokens import Token, update_user_token
from lms.models.users import User

FAKE_ACCESS_TOKEN = "FAKE_TOKEN"

class TestApplicationInstance(object):
    def test_it_updates_none_token(self, db_session):
        user = User()
        db_session.add(user)
        db_session.flush()
    
        token = Token(access_token = FAKE_ACCESS_TOKEN)
        update_user_token(db_session, token, user)
        
        db_session.flush()
        assert user.id != None
        assert token.user_id == user.id
        
    def test_it_updates_some_token(self, db_session):
        user = User()
        db_session.add(user)
        db_session.flush()
    
        token = Token(access_token = FAKE_ACCESS_TOKEN)
        update_user_token(db_session, token, user)
        
        db_session.flush()

        another_token = Token(access_token = "ANOTHER_FAKE_ACCESS_TOKEN")
        updated_token = update_user_token(db_session, another_token, user)

        db_session.flush()

        assert user.id != None
        assert updated_token.user_id == user.id
        assert updated_token.access_token == "ANOTHER_FAKE_ACCESS_TOKEN"

