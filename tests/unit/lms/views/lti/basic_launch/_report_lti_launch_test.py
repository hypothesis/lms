import pytest
from pyramid.testing import DummyRequest

from lms.models import LtiLaunches
from lms.views.lti.basic_launch import BasicLTILaunchViews


class TestReportLTILaunch:
    def test_it_adds_an_lti_launch_record_to_the_db(self, pyramid_request):
        BasicLTILaunchViews._report_lti_launch(pyramid_request)

        lti_launch = pyramid_request.db.query(LtiLaunches).one()
        assert lti_launch.context_id == "TEST_CONTEXT_ID"
        assert lti_launch.lti_key == "TEST_OAUTH_CONSUMER_KEY"

    @pytest.fixture
    def pyramid_request(self):
        return DummyRequest(
            params={
                "context_id": "TEST_CONTEXT_ID",
                "oauth_consumer_key": "TEST_OAUTH_CONSUMER_KEY",
            }
        )
