from contextlib import contextmanager
from datetime import datetime
from unittest.mock import call, sentinel

import celery
import pytest
from freezegun import freeze_time

from lms.tasks.email_digests import (
    send_instructor_email_digest,
    send_instructor_email_digest_tasks,
)
from tests import factories


class TestSendInstructorEmailDigestsTasks:
    def test_it_does_nothing_if_there_are_no_instructors(
        self, send_instructor_email_digest
    ):
        send_instructor_email_digest_tasks(batch_size=42)

        send_instructor_email_digest.apply_async.assert_not_called()

    @freeze_time("2023-03-09 05:15:00")
    def test_it_sends_digests_for_instructors(
        self, send_instructor_email_digest, participating_instructors
    ):
        send_instructor_email_digest_tasks(batch_size=3)

        assert send_instructor_email_digest.apply_async.call_args_list == [
            call(
                (),
                {
                    "h_userid": participating_instructor.h_userid,
                    "created_after": "2023-03-08T05:00:00",
                    "created_before": "2023-03-09T05:00:00",
                },
            )
            for participating_instructor in participating_instructors
        ]

    @pytest.mark.usefixtures("participating_instructors_with_no_launches")
    def test_it_doesnt_email_for_courses_with_no_launches(
        self, send_instructor_email_digest
    ):
        send_instructor_email_digest_tasks(batch_size=42)

        send_instructor_email_digest.apply_async.assert_not_called()

    @pytest.mark.usefixtures("non_participating_instructor")
    def test_it_doesnt_email_non_participating_instructors(
        self, send_instructor_email_digest
    ):
        send_instructor_email_digest_tasks(batch_size=42)

        send_instructor_email_digest.apply_async.assert_not_called()

    @pytest.mark.usefixtures("non_instructor")
    def test_it_doesnt_email_non_instructors(self, send_instructor_email_digest):
        send_instructor_email_digest_tasks(batch_size=42)

        send_instructor_email_digest.apply_async.assert_not_called()

    @freeze_time("2023-03-09 05:15:00")
    def test_it_doesnt_email_unsubscribed_instructors(
        self, send_instructor_email_digest, participating_instructors
    ):
        participating_instructors, unsubscribed_instructors = (
            participating_instructors[:1],
            participating_instructors[1:],
        )
        for unsubscribed_instructor in unsubscribed_instructors:
            factories.UserPreferences(
                h_userid=unsubscribed_instructor.h_userid,
                preferences={"instructor_email_digests.days.thu": False},
            )

        send_instructor_email_digest_tasks(
            batch_size=len(participating_instructors + unsubscribed_instructors)
        )

        emailed_huserids = [
            call[0][1]["h_userid"]
            for call in send_instructor_email_digest.apply_async.call_args_list
        ]
        assert not any(
            unsubscribed_instructor.h_userid in emailed_huserids
            for unsubscribed_instructor in unsubscribed_instructors
        )

    @freeze_time("2023-03-09 05:15:00")
    def test_it_deduplicates_duplicate_h_userids(
        self, send_instructor_email_digest, participating_instructors, make_instructors
    ):
        # Make a user with the same h_userid as another user but
        # a different application instance.
        user = participating_instructors[0]
        instance = participating_instructors[-1].application_instance
        assert instance != user.application_instance
        duplicate_user = factories.User(
            h_userid=user.h_userid, application_instance=instance
        )
        make_instructors([duplicate_user], instance)

        send_instructor_email_digest_tasks(batch_size=99)

        emailed_huserids = [
            call[0][1]["h_userid"]
            for call in send_instructor_email_digest.apply_async.call_args_list
        ]
        assert emailed_huserids.count(duplicate_user.h_userid) == 1

    @pytest.fixture
    def participating_instances(self):
        """Return some instances that have the feature enabled."""
        instances = factories.ApplicationInstance.create_batch(2)

        for instance in instances:
            instance.settings.set(
                "hypothesis", "instructor_email_digests_enabled", True
            )

        return instances

    @pytest.fixture
    def participating_instructors(self, participating_instances, make_instructors):
        """Return some users who're instructors in participating instances."""
        users = []

        for instance in participating_instances:
            for _ in range(2):
                users.append(factories.User(application_instance=instance))

        make_instructors(users, participating_instances[0], with_launch=True)

        return sorted(users, key=lambda u: u.h_userid)

    @pytest.fixture
    def participating_instructors_with_no_launches(
        self, participating_instances, make_instructors
    ):
        """Return some users who're instructors in participating instances."""
        users = []

        for instance in participating_instances:
            for _ in range(2):
                users.append(factories.User(application_instance=instance))

        make_instructors(users, participating_instances[0], with_launch=False)

        return sorted(users, key=lambda u: u.h_userid)

    @pytest.fixture
    def non_participating_instance(self):
        """Return an instance that doesn't have the feature enabled."""
        instance = factories.ApplicationInstance()
        instance.settings.set("hypothesis", "instructor_email_digests_enabled", False)
        return instance

    @pytest.fixture
    def non_participating_instructor(
        self, non_participating_instance, make_instructors
    ):
        """Return a user who's an instructor in a non-participating instance."""
        user = factories.User(application_instance=non_participating_instance)
        make_instructors([user], non_participating_instance)
        return user

    @pytest.fixture
    def non_instructor(self, participating_instances, make_learner):
        """Return a user who isn't an instructor."""
        user = factories.User(application_instance=participating_instances[0])
        make_learner(user)
        return user

    @pytest.fixture
    def make_instructors(self, db_session):
        instructor_role = factories.LTIRole(value="Instructor")

        def make_instructors(users, application_instance, with_launch=True):
            """Make the given user instructors for an assignment."""
            course = factories.Course()
            assignment = factories.Assignment()
            factories.AssignmentGrouping(grouping=course, assignment=assignment)

            if with_launch:
                # Create a launch for this course/assignment
                factories.Event(
                    timestamp=datetime(2023, 3, 8, 22),
                    application_instance=application_instance,
                    course=course,
                    assignment=assignment,
                )
            for user in users:
                factories.AssignmentMembership(
                    assignment=assignment, user=user, lti_role=instructor_role
                )
            db_session.flush()

        return make_instructors

    @pytest.fixture
    def make_learner(self, db_session):
        learner_role = factories.LTIRole(value="Learner")

        def make_learner(user):
            """Make the given user a learner for an assignment."""
            factories.AssignmentMembership(
                assignment=factories.Assignment(), user=user, lti_role=learner_role
            )
            db_session.flush()

        return make_learner

    @pytest.fixture(autouse=True)
    def retry(self, patch):
        return patch(
            "lms.tasks.email_digests.send_instructor_email_digest_tasks.retry",
            side_effect=celery.exceptions.Retry,
        )

    @pytest.fixture(autouse=True)
    def send_instructor_email_digest(self, patch):
        return patch("lms.tasks.email_digests.send_instructor_email_digest")


@pytest.mark.usefixtures("digest_service")
class TestSendInstructorEmailDigests:
    def test_it(self, digest_service):
        created_after = datetime(year=2023, month=3, day=1)
        created_before = datetime(year=2023, month=3, day=2)

        send_instructor_email_digest(
            h_userid=sentinel.h_userid,
            created_after=created_after.isoformat(),
            created_before=created_before.isoformat(),
            override_to_email=sentinel.override_to_email,
        )

        digest_service.send_instructor_email_digest.assert_called_once_with(
            sentinel.h_userid,
            created_after,
            created_before,
            override_to_email=sentinel.override_to_email,
        )

    @pytest.mark.parametrize(
        "created_after,created_before",
        [
            ("invalid", "2023-02-28T00:00:00"),
            ("2023-02-28T00:00:00", "invalid"),
            ("invalid", "invalid"),
        ],
    )
    def test_it_crashes_if_created_after_or_created_before_is_invalid(
        self, created_after, created_before
    ):
        with pytest.raises(ValueError, match="^Invalid isoformat string"):
            send_instructor_email_digest(
                h_userid=sentinel.h_userid,
                created_after=created_after,
                created_before=created_before,
            )


@pytest.fixture(autouse=True)
def app(patch, pyramid_request):
    app = patch("lms.tasks.email_digests.app")

    @contextmanager
    def request_context():
        yield pyramid_request

    app.request_context = request_context

    return app
