from contextlib import contextmanager

import pytest

from lms.tasks.course_roster import fetch_roster
from tests import factories


class TestFetchRoster:
    def test_it(self, course_roster_service, db_session):
        lms_course = factories.LMSCourse()
        db_session.flush()

        fetch_roster(lms_course_id=lms_course.id)

        course_roster_service.fetch_roster.assert_called_once_with(lms_course)


@pytest.fixture(autouse=True)
def app(patch, pyramid_request):
    app = patch("lms.tasks.course_roster.app")

    @contextmanager
    def request_context():
        yield pyramid_request

    app.request_context = request_context

    return app
