from contextlib import contextmanager
from datetime import datetime

import pytest
from freezegun import freeze_time

from lms.tasks.roster import (
    fetch_assignment_roster,
    fetch_canvas_sections_roster,
    fetch_course_roster,
    fetch_segment_roster,
    schedule_fetching_assignment_rosters,
    schedule_fetching_course_rosters,
    schedule_fetching_rosters,
    schedule_fetching_segment_rosters,
)
from tests import factories


class TestRosterTasks:
    def test_fetch_course_roster(self, roster_service, db_session):
        lms_course = factories.LMSCourse()
        db_session.flush()

        fetch_course_roster(lms_course_id=lms_course.id)

        roster_service.fetch_course_roster.assert_called_once_with(lms_course)

    def test_fetch_course_roster_with_sections(
        self, roster_service, db_session, fetch_canvas_sections_roster
    ):
        lms_course = factories.LMSCourse()
        factories.LMSSegment(lms_course=lms_course, type="canvas_section")
        db_session.flush()

        fetch_course_roster(lms_course_id=lms_course.id)

        roster_service.fetch_course_roster.assert_called_once_with(lms_course)
        fetch_canvas_sections_roster.delay.assert_called_once_with(
            lms_course_id=lms_course.id
        )

    def test_fetch_assignment_roster(self, roster_service, db_session):
        assignment = factories.Assignment()
        db_session.flush()

        fetch_assignment_roster(assignment_id=assignment.id)

        roster_service.fetch_assignment_roster.assert_called_once_with(assignment)

    def test_fetch_segment_roster(self, roster_service, db_session):
        lms_segment = factories.LMSSegment()
        db_session.flush()

        fetch_segment_roster(lms_segment_id=lms_segment.id)

        roster_service.fetch_canvas_group_roster.assert_called_once_with(lms_segment)

    def test_fetch_canvas_sections_roster(self, roster_service, db_session):
        lms_course = factories.LMSCourse()
        db_session.flush()

        fetch_canvas_sections_roster(lms_course_id=lms_course.id)

        roster_service.fetch_canvas_sections_roster.assert_called_once_with(lms_course)

    def test_schedule_fetching_rosters(
        self,
        schedule_fetching_assignment_rosters,
        schedule_fetching_course_rosters,
        schedule_fetching_segment_rosters,
    ):
        schedule_fetching_rosters()

        schedule_fetching_course_rosters.assert_called_once_with()
        schedule_fetching_assignment_rosters.assert_called_once_with()
        schedule_fetching_segment_rosters.assert_called_once_with()

    @freeze_time("2024-08-28")
    @pytest.mark.usefixtures(
        "lms_course_with_no_launch",
        "lms_course_with_no_recent_launch",
        "lms_course_with_no_service_url",
        "lms_course_with_launch_and_recent_roster",
        "lms_course_with_recent_launch_and_task_done_row",
    )
    def test_schedule_fetching_course_rosters(
        self, lms_course_with_recent_launch, db_session, fetch_course_roster
    ):
        db_session.flush()

        schedule_fetching_course_rosters()

        fetch_course_roster.delay.assert_called_once_with(
            lms_course_id=lms_course_with_recent_launch.id
        )

    @freeze_time("2024-08-28")
    @pytest.mark.usefixtures(
        "assignment_with_no_launch",
        "assignment_with_no_recent_launch",
        "assignment_with_no_lti_v13_id",
        "assignment_with_recent_launch_and_task_done_row",
        "assignment_with_launch_and_recent_roster",
    )
    def test_schedule_fetching_assignment_rosters(
        self, assignment_with_recent_launch, db_session, fetch_assignment_roster
    ):
        db_session.flush()

        schedule_fetching_assignment_rosters()

        fetch_assignment_roster.delay.assert_called_once_with(
            assignment_id=assignment_with_recent_launch.id
        )

    @freeze_time("2024-08-28")
    @pytest.mark.usefixtures(
        "lms_segment_with_no_launch",
        "lms_segment_with_no_recent_launch",
        "lms_segment_with_recent_launch_and_task_done_row",
        "lms_segment_with_launch_and_recent_roster",
    )
    def test_schedule_fetching_segment_rosters(
        self, lms_segment_with_recent_launch, db_session, fetch_segment_roster
    ):
        db_session.flush()

        schedule_fetching_segment_rosters()

        fetch_segment_roster.delay.assert_called_once_with(
            lms_segment_id=lms_segment_with_recent_launch.id
        )

    @pytest.fixture
    def lms_course_with_no_service_url(self):
        return factories.LMSCourse()

    @pytest.fixture
    def assignment_with_no_lti_v13_id(self):
        return factories.LMSCourse()

    @pytest.fixture
    def lms_course_with_no_launch(self):
        return factories.LMSCourse(lti_context_memberships_url="URL")

    @pytest.fixture
    def assignment_with_no_launch(self):
        return factories.Assignment(
            lti_v13_resource_link_id="ID", course=factories.Course()
        )

    @pytest.fixture
    def assignment_with_no_recent_launch(self, lms_course_with_recent_launch):
        assignment = factories.Assignment(
            lti_v13_resource_link_id="ID", course=lms_course_with_recent_launch.course
        )
        factories.Event(
            assignment=assignment,
            timestamp=datetime(2024, 1, 1),  # noqa: DTZ001
        )
        return assignment

    @pytest.fixture
    def lms_course_with_recent_launch(self):
        course = factories.Course()
        factories.Event(
            course=course,
            timestamp=datetime(2024, 8, 28),  # noqa: DTZ001
        )

        return factories.LMSCourse(
            lti_context_memberships_url="URL",
            h_authority_provided_id=course.authority_provided_id,
            course=course,
        )

    @pytest.fixture
    def lms_course_with_no_recent_launch(self):
        course = factories.Course()
        factories.Event(
            course=course,
            timestamp=datetime(2024, 1, 1),  # noqa: DTZ001
        )

        return factories.LMSCourse(
            lti_context_memberships_url="URL",
            h_authority_provided_id=course.authority_provided_id,
            course=course,
        )

    @pytest.fixture
    def lms_course_with_recent_launch_and_task_done_row(self, db_session):
        course = factories.Course()
        factories.Event(
            course=course,
            timestamp=datetime(2024, 8, 28),  # noqa: DTZ001
        )
        lms_course = factories.LMSCourse(
            lti_context_memberships_url="URL",
            h_authority_provided_id=course.authority_provided_id,
            course=course,
        )
        db_session.flush()  # Make sure we have an ID for the course
        factories.TaskDone(key=f"roster::course::scheduled::{lms_course.id}")
        return lms_course

    @pytest.fixture
    def assignment_with_recent_launch(self, lms_course_with_recent_launch):
        assignment = factories.Assignment(
            lti_v13_resource_link_id="ID", course=lms_course_with_recent_launch.course
        )
        factories.Event(
            assignment=assignment,
            timestamp=datetime(2024, 8, 28),  # noqa: DTZ001
        )
        return assignment

    @pytest.fixture
    def assignment_with_recent_launch_and_task_done_row(
        self, lms_course_with_recent_launch, db_session
    ):
        assignment = factories.Assignment(
            lti_v13_resource_link_id="ID", course=lms_course_with_recent_launch.course
        )
        factories.Event(
            assignment=assignment,
            timestamp=datetime(2024, 8, 28),  # noqa: DTZ001
        )
        db_session.flush()  # Make sure we have an ID for the assignment
        factories.TaskDone(key=f"roster::assignment::scheduled::{assignment.id}")
        return assignment

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
            updated=datetime(2024, 8, 25),  # noqa: DTZ001
        )

        return lms_course

    @pytest.fixture
    def assignment_with_launch_and_recent_roster(self, lms_course_with_recent_launch):
        assignment = factories.Assignment(
            lti_v13_resource_link_id="ID", course=lms_course_with_recent_launch.course
        )
        factories.Event(
            assignment=assignment,
            timestamp=datetime(2024, 8, 28),  # noqa: DTZ001
        )
        factories.AssignmentRoster(
            assignment=assignment,
            lms_user=factories.LMSUser(),
            lti_role=factories.LTIRole(),
            active=True,
            updated=datetime(2024, 8, 25),  # noqa: DTZ001
        )

        return assignment

    @pytest.fixture
    def lms_segment_with_no_launch(self, lms_course_with_no_launch):
        return factories.LMSSegment(
            lms_course=lms_course_with_no_launch, type="canvas_group"
        )

    @pytest.fixture
    def lms_segment_with_no_recent_launch(self, lms_course_with_no_recent_launch):
        return factories.LMSSegment(
            lms_course=lms_course_with_no_recent_launch, type="canvas_group"
        )

    @pytest.fixture
    def lms_segment_with_recent_launch(self, lms_course_with_recent_launch):
        return factories.LMSSegment(
            lms_course=lms_course_with_recent_launch, type="canvas_group"
        )

    @pytest.fixture
    def lms_segment_with_recent_launch_and_task_done_row(
        self, lms_course_with_recent_launch, db_session
    ):
        lms_segment = factories.LMSSegment(
            lms_course=lms_course_with_recent_launch, type="canvas_group"
        )
        db_session.flush()  # Make sure we have an ID for the course
        factories.TaskDone(key=f"roster::segment::scheduled::{lms_segment.id}")

        return lms_segment

    @pytest.fixture
    def lms_segment_with_launch_and_recent_roster(self, lms_course_with_recent_launch):
        lms_segment = factories.LMSSegment(
            lms_course=lms_course_with_recent_launch, type="canvas_group"
        )
        factories.LMSSegmentRoster(
            lms_segment=lms_segment,
            lms_user=factories.LMSUser(),
            lti_role=factories.LTIRole(),
            active=True,
            updated=datetime(2024, 8, 25),  # noqa: DTZ001
        )

        return lms_segment

    @pytest.fixture
    def fetch_course_roster(self, patch):
        return patch("lms.tasks.roster.fetch_course_roster")

    @pytest.fixture
    def fetch_assignment_roster(self, patch):
        return patch("lms.tasks.roster.fetch_assignment_roster")

    @pytest.fixture
    def fetch_segment_roster(self, patch):
        return patch("lms.tasks.roster.fetch_segment_roster")

    @pytest.fixture
    def fetch_canvas_sections_roster(self, patch):
        return patch("lms.tasks.roster.fetch_canvas_sections_roster")

    @pytest.fixture
    def schedule_fetching_segment_rosters(self, patch):
        return patch("lms.tasks.roster.schedule_fetching_segment_rosters")

    @pytest.fixture
    def schedule_fetching_assignment_rosters(self, patch):
        return patch("lms.tasks.roster.schedule_fetching_assignment_rosters")

    @pytest.fixture
    def schedule_fetching_course_rosters(self, patch):
        return patch("lms.tasks.roster.schedule_fetching_course_rosters")


@pytest.fixture(autouse=True)
def app(patch, pyramid_request):
    app = patch("lms.tasks.roster.app")

    @contextmanager
    def request_context():
        yield pyramid_request

    app.request_context = request_context

    return app
