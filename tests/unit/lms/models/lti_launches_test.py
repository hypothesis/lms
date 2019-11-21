from lms.models import LtiLaunches


class TestLTILaunches:
    def test_add_adds_an_lti_launch_record_to_the_db(self, db_session):
        LtiLaunches.add(db_session, "TEST_CONTEXT_ID", "TEST_OAUTH_CONSUMER_KEY")

        lti_launch = db_session.query(LtiLaunches).one()
        assert lti_launch.context_id == "TEST_CONTEXT_ID"
        assert lti_launch.lti_key == "TEST_OAUTH_CONSUMER_KEY"
