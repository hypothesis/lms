import sqlalchemy as sa
from lms.db import BASE


class User(BASE):

    __tablename__ = 'users'

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)

    lms_guid = sa.Column(sa.String, index=True)


def find_by_lms_guid(session, lms_guid):
  return session.query(User).filter(
    User.lms_guid == lms_guid).one_or_none()


def build_from_lti_params(lti_launch_params):
    return User(
      lms_guid=lti_launch_params['user_id'],
    )
