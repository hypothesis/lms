import json
from lms.models.tokens import Token, update_user_token
from lms.models.users import User, build_from_lti_params
from lms.models.application_instance import ApplicationInstance
from lms.models.oauth_state import OauthState, find_or_create_from_user


class TestOauthState(object):
    def test_find_or_create_from_user_creates_user(self, lti_launch_request, db_session):
        session = db_session
        state_guid = "asdf"
        user = build_from_lti_params(lti_launch_request.params)
        session.add(user)
        session.flush()
        lti_params = json.dumps(dict(lti_launch_request.params))

        result = find_or_create_from_user(db_session, state_guid, user, lti_params)

        assert user.id == result.user_id
        assert result.lti_params == result.lti_params
        assert result.guid == state_guid

    def test_find_or_create_from_user_creates_user(self, lti_launch_request, db_session):
        session = db_session
        state_guid = "asdf"
        user = build_from_lti_params(lti_launch_request.params)
        session.add(user)
        session.flush()
        lti_params = json.dumps(dict(lti_launch_request.params))

        existing_state = OauthState(user_id=user.id, guid=state_guid, lti_params=lti_params)
        session.add(existing_state)
        session.flush()

        result = find_or_create_from_user(db_session, state_guid, user, lti_params)

        assert result.id == existing_state.id
