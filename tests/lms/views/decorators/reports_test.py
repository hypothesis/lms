from unittest import mock

import pytest
from pyramid.testing import DummyRequest

from lms.models.lti_launches import LtiLaunches
from lms.views.decorators.reports import report_lti_launch


class TestReportLTILaunch:
    def test_it_adds_an_lti_launch_record_to_the_db(self, pyramid_request, wrapped):
        report_lti_launch(wrapped)(mock.sentinel.context, pyramid_request)

        lti_launch = pyramid_request.db.query(LtiLaunches).one()
        assert lti_launch.context_id == "TEST_CONTEXT_ID"
        assert lti_launch.lti_key == "TEST_OAUTH_CONSUMER_KEY"

    def test_it_calls_the_decorated_view(self, pyramid_request, wrapped):
        result = report_lti_launch(wrapped)(mock.sentinel.context, pyramid_request)

        wrapped.assert_called_once_with(mock.sentinel.context, pyramid_request)
        assert result == wrapped.return_value

    @pytest.fixture
    def pyramid_request(self):
        return DummyRequest(
            params={
                "context_id": "TEST_CONTEXT_ID",
                "oauth_consumer_key": "TEST_OAUTH_CONSUMER_KEY",
            }
        )

    @pytest.fixture
    def wrapped(self):
        """The wrapped view callable."""

        def view_callable_spec(context, request):
            """Spec for the mock view callable."""

        return mock.create_autospec(view_callable_spec, spec_set=True)
