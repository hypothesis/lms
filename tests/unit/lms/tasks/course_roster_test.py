from contextlib import contextmanager
from datetime import datetime

import pytest
from freezegun import freeze_time

from lms.tasks.course_roster import fetch_roster, schedule_fetching_rosters
from tests import factories


class TestFetchRoster:
    def test_it(self, course_roster_service, db_session):
        lms_course = factories.LMSCourse()
        db_session.flush()

        fetch_roster(lms_course_id=lms_course.id)

        course_roster_service.fetch_roster.assert_called_once_with(lms_course)


@freeze_time("2024-08-28")
class TestScheduleFetchingRosters:
    @pytest.mark.usefixtures(
        "lms_course_with_no_launch",
        "lms_course_with_no_service_url",
        "lms_course_with_launch_and_recent_roster",
    )
    def test_it(self, lms_course_with_recent_launch, db_session, fetch_roster):
        db_session.flush()

        schedule_fetching_rosters()

        fetch_roster.delay.assert_called_once_with(
            lms_course_id=lms_course_with_recent_launch.id
        )

    @pytest.fixture
    def lms_course_with_no_service_url(self):
        return factories.LMSCourse()

    @pytest.fixture
    def lms_course_with_no_launch(self):
        return factories.LMSCourse(lti_context_memberships_url="URL")

    @pytest.fixture
    def lms_course_with_recent_launch(self):
        course = factories.Course()
        factories.Event(
            course=course,
            timestamp=datetime(2024, 8, 28),
        )

        return factories.LMSCourse(
            lti_context_memberships_url="URL",
            h_authority_provided_id=course.authority_provided_id,
        )

    @pytest.fixture
    def lms_course_with_launch_and_recent_roster(self):
        course = factories.Course()
        factories.Event(course=course)
        lms_course = factories.LMSCourse(
            lti_context_memberships_url="URL",
            h_authority_provided_id=course.authority_provided_id,
        )
        factories.CourseRoster(
            lms_course=lms_course,
            lms_user=factories.LMSUser(),
            lti_role=factories.LTIRole(),
            active=True,
            updated=datetime(2024, 8, 25),
        )

        return lms_course

    @pytest.fixture
    def fetch_roster(self, patch):
        return patch("lms.tasks.course_roster.fetch_roster")


@pytest.fixture(autouse=True)
def app(patch, pyramid_request):
    app = patch("lms.tasks.course_roster.app")

    @contextmanager
    def request_context():
        yield pyramid_request

    app.request_context = request_context

    return app
