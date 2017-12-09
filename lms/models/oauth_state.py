import sqlalchemy as sa
from lms.db import BASE
from lms.models.users import User


class OauthState(BASE):

    __tablename__ = 'oauth_state'

    id = sa.Column(sa.Integer, autoincrement=True, primary_key=True)
    user_id = sa.Column(sa.Integer)
    guid = sa.Column(sa.String)
    lti_params = sa.Column(sa.String)


def find_by_state(session, state):
    return session.query(OauthState).filter(
        OauthState.guid == state).one_or_none()


def find_or_create_from_user(session, state, user, lti_params):
    existing_state = find_by_state(session, state)
    if existing_state is None:
        oauth_state = OauthState(user_id=user.id, guid=state, lti_params=lti_params)
        session.add(oauth_state)
        return oauth_state
    return existing_state


def find_user_from_state(session, state):
    state = find_by_state(session, state)
    if state is None:
        return None
    return session.query(User).filter(User.id == state.user_id).one_or_none()
