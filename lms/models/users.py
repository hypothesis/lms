import sqlalchemy as sa
from lms.db import BASE


class User(BASE):
    """Class that links a document url to a specific lms module (Not needed for canvas)."""

    __tablename__ = 'users'

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    email = sa.Column(sa.String)
    lms_id = sa.Column(sa.String)
    lms_provider = sa.Column(sa.String)
    lms_url = sa.Column(sa.String)
