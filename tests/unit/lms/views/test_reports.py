from lms.models import LtiLaunches
from lms.views.reports import list_application_instances
from tests import factories


def setup_launches(pyramid_request, app_instances):
    pyramid_request.db.add_all(
        [
            LtiLaunches(context_id="asdf", lti_key=app_instances[0].consumer_key),
            LtiLaunches(context_id="asdf", lti_key=app_instances[0].consumer_key),
            LtiLaunches(context_id="asdf", lti_key=app_instances[0].consumer_key),
            LtiLaunches(context_id="fdsa", lti_key=app_instances[1].consumer_key),
            LtiLaunches(context_id="another", lti_key=app_instances[2].consumer_key),
            LtiLaunches(context_id="another", lti_key=app_instances[2].consumer_key),
        ]
    )

    pyramid_request.db.flush()


class TestReports:
    def test_build_launches_rows(self, pyramid_request):
        app_instances = factories.ApplicationInstance.create_batch(size=3)
        setup_launches(pyramid_request, app_instances)

        result = list_application_instances(pyramid_request)

        assert result["num_launches"] == 6
        assert sorted(result["launches"], key=lambda result: result[1]) == [
            (
                "fdsa",
                1,
                app_instances[1].lms_url,
                app_instances[1].requesters_email,
                app_instances[1].consumer_key,
            ),
            (
                "another",
                2,
                app_instances[2].lms_url,
                app_instances[2].requesters_email,
                app_instances[2].consumer_key,
            ),
            (
                "asdf",
                3,
                app_instances[0].lms_url,
                app_instances[0].requesters_email,
                app_instances[0].consumer_key,
            ),
        ]
