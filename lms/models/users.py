import sqlalchemy as sa
from lms.db import BASE


class User(BASE):
    """Class to represent a single lti user."""

    __tablename__ = "users"

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    lms_guid = sa.Column(sa.String, index=True)


def find_by_lms_guid(session, user_lms_guid):
    """Find a user from their unique lti launch user_id guid."""
    return session.query(User).filter(User.lms_guid == user_lms_guid).one_or_none()


def build_from_lti_params(lti_launch_params):
    """Build a user from an lti launch POST request."""
    return User(lms_guid=lti_launch_params["user_id"])
