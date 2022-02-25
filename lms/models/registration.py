import sqlalchemy as sa

from lms.db import BASE


class Registration(BASE):
    __tablename__ = "registration"
    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)

    # TODO unique together
    issuer = sa.Column(sa.UnicodeText, nullable=True)
    client_id = sa.Column(sa.UnicodeText, nullable=True)

    key_set_url = sa.Column(sa.UnicodeText, nullable=True)
    auth_login_url = sa.Column(sa.UnicodeText, nullable=True)
