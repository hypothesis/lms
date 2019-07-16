from lms.views.reports import list_application_instances
from lms.models import ApplicationInstance
from lms.models import LtiLaunches


def setup_launches(pyramid_request, app_instances):
    launch1 = LtiLaunches(context_id="asdf", lti_key=app_instances[0].consumer_key)
    launch2 = LtiLaunches(context_id="asdf", lti_key=app_instances[0].consumer_key)
    launch3 = LtiLaunches(context_id="asdf", lti_key=app_instances[0].consumer_key)
    launch4 = LtiLaunches(context_id="fdsa", lti_key=app_instances[1].consumer_key)
    launch5 = LtiLaunches(context_id="another", lti_key=app_instances[2].consumer_key)
    launch6 = LtiLaunches(context_id="another", lti_key=app_instances[2].consumer_key)

    for launch in [launch1, launch2, launch3, launch4, launch5, launch6]:
        pyramid_request.db.add(launch)
    pyramid_request.db.flush()


class TestReports:
    def test_build_launches_rows(self, pyramid_request):
        test_urls = [
            "https://example.com",
            "https://sub.example.com",
            "https://another.example.com",
        ]
        test_emails = ["a@example.com", "b@sub.example.com", "c@another.example.com"]

        def build_ai_from_pair(pair):
            return ApplicationInstance.build_from_lms_url(
                pair[0], pair[1], None, None, None
            )

        app_instances = list(map(build_ai_from_pair, zip(test_urls, test_emails)))
        for app in app_instances:
            pyramid_request.db.add(app)

        setup_launches(pyramid_request, app_instances)

        result = list_application_instances(pyramid_request)
        assert result["num_launches"] == 6
        assert result["launches"] == [
            (
                "asdf",
                3,
                "https://example.com",
                "a@example.com",
                app_instances[0].consumer_key,
            ),
            (
                "another",
                2,
                "https://another.example.com",
                "c@another.example.com",
                app_instances[2].consumer_key,
            ),
            (
                "fdsa",
                1,
                "https://sub.example.com",
                "b@sub.example.com",
                app_instances[1].consumer_key,
            ),
        ]
