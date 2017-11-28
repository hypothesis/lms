import sqlalchemy as sa
from lms.db import BASE


class OauthState(BASE):

    __tablename__ = 'oauth_states'

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    user_id = sa.Column(sa.Integer)
    guid = sa.Column(sa.String)
