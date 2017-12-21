from datetime import datetime
import sqlalchemy as sa
from lms.db import BASE


class Token(BASE):
    """Class to represent an lms api token."""

    __tablename__ = 'tokens'

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    access_token = sa.Column(sa.String)
    refresh_token = sa.Column(sa.String)
    expires_in = sa.Column(sa.String)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'))
    created = sa.Column(sa.TIMESTAMP, default=datetime.utcnow)


def find_token_by_user_id(session, user_id):
    """Find a user by their id."""
    return session.query(Token).filter(Token.user_id == user_id).one_or_none()


def build_token_from_oauth_response(oauth_resp):
    """Build a token from an oauth response."""
    return Token(
        access_token=oauth_resp['access_token'],
        refresh_token=oauth_resp['refresh_token'],
        expires_in=oauth_resp['expires_in'],
    )


def update_user_token(session, new_token, user):
    """
    Update a user token.

    Either associate the provided token with
    the provided user or update the user's token
    to reflect the data in the provided token
    """
    token = find_token_by_user_id(session, user.id)

    if token is None:
        new_token.user_id = user.id
        session.add(new_token)
        return new_token

    token.access_token = new_token.access_token
    token.refresh_token = new_token.refresh_token
    token.expires_in = new_token.expires_in

    return token
