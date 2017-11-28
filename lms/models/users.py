import sqlalchemy as sa
from lms.db import BASE


class Token(BASE):

    __tablename__ = 'tokens'

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    access_token = sa.Column(sa.String)
    refresh_token = sa.Column(sa.String)
    expires_at = sa.Column(sa.String)
    user_id = sa.Column(sa.String)

