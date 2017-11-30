import sqlalchemy as sa
from lms.db import BASE
from datetime import datetime


class Token(BASE):

    __tablename__ = 'tokens'

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    access_token = sa.Column(sa.String)
    refresh_token = sa.Column(sa.String)
    expires_in = sa.Column(sa.String)
    user_id = sa.Column(sa.Integer)
    created = sa.Column(sa.TIMESTAMP, default=datetime.utcnow)

def find_or_create(session, token, user):
    pass

def find_token_by_user_id(session, user_id):
    return session.query(Token).filter(Token.user_id == user_id).one_or_none()

def build_token_from_oauth_response(oauth_resp):
    return Token(
        access_token=oauth_resp['access_token'],
        refresh_token=oauth_resp['refresh_token'],
        expires_in=oauth_resp['expires_in'],
    )
def update_user_token(session, oauth_resp, user):
    token = find_token_by_user_id(session, user.id)

    if(token == None):
        new_token = build_token_from_oauth_response(oauth_resp)
        session.add(new_token)
        return new_token
    token.access_token = oauth_resp['access_token']
    token.refresh_token = oauth_resp['refresh_token']
    token.expires_in = oauth_resp['expires_in']

    return token
