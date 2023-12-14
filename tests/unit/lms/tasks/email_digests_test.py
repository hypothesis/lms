from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
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
        send_instructor_email_digest_tasks()

        send_instructor_email_digest.apply_async.assert_not_called()

    @freeze_time("2023-03-09 05:15:00")
    def test_it_sends_digests_for_instructors(
        self, send_instructor_email_digest, participating_instructors
    ):
        send_instructor_email_digest_tasks()

        assert send_instructor_email_digest.apply_async.call_args_list == [
            call(
                (),
                {
                    "h_userid": participating_instructor.h_userid,
                    "created_before": "2023-03-09T05:00:00+00:00",
                },
            )
            for participating_instructor in participating_instructors
        ]

    @pytest.mark.usefixtures("participating_instructors_with_no_launches")
    def test_it_doesnt_email_for_courses_with_no_launches(
        self, send_instructor_email_digest
    ):
        send_instructor_email_digest_tasks()

        send_instructor_email_digest.apply_async.assert_not_called()

    @pytest.mark.usefixtures("non_participating_instructor")
    def test_it_doesnt_email_non_participating_instructors(
        self, send_instructor_email_digest
    ):
        send_instructor_email_digest_tasks()

        send_instructor_email_digest.apply_async.assert_not_called()

    @pytest.mark.usefixtures("non_instructor")
    def test_it_doesnt_email_non_instructors(self, send_instructor_email_digest):
        send_instructor_email_digest_tasks()

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

        send_instructor_email_digest_tasks()

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

        send_instructor_email_digest_tasks()

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
    def test_it(
        self, created_before, digest_service, db_session, h_userid, make_task_done
    ):
        # The TaskDone that we expect get_task_done() to return.
        matching_task_done = make_task_done(created_before=created_before.isoformat())

        db_session.add_all(
            [
                # An older TaskDone for the same user, this should be ignored.
                make_task_done(
                    created_before=(created_before - timedelta(days=1)).isoformat()
                ),
                # A TaskDone with a different type, this should be ignored.
                make_task_done(type="DIFFERENT"),
                # A TaskDone with a different h_userid, this should be ignored.
                make_task_done(h_userid="DIFFERENT"),
                # A TaskDone with None in the data column, this should be ignored.
                factories.TaskDone(data=None),
                # A TaskDone with no h_userid, this should be ignored.
                make_task_done(omit=["h_userid"]),
                # A TaskDone with no created_before, this should be ignored.
                make_task_done(omit=["created_before"]),
                # A TaskDone with an invalid created_before, this should be ignored.
                make_task_done(created_before="foo"),
                # The TaskDone that we expect get_task_done() to return.
                matching_task_done,
            ]
        )

        send_instructor_email_digest(
            h_userid=h_userid,
            created_before=created_before.isoformat(),
            override_to_email=sentinel.override_to_email,
        )

        digest_service.send_instructor_email_digest.assert_called_once_with(
            h_userid,
            datetime.fromisoformat(matching_task_done.data["created_before"]),
            created_before,
            override_to_email=sentinel.override_to_email,
        )

    def test_it_when_theres_no_matching_TaskDone(
        self, created_before, digest_service, h_userid
    ):
        send_instructor_email_digest(
            h_userid=h_userid, created_before=created_before.isoformat()
        )

        digest_service.send_instructor_email_digest.assert_called_once_with(
            h_userid, created_before - timedelta(days=7), created_before
        )

    def test_it_when_TaskDone_is_more_than_a_week_old(
        self, created_before, db_session, digest_service, h_userid, make_task_done
    ):
        db_session.add(
            make_task_done(
                created_before=(created_before - timedelta(days=8)).isoformat()
            )
        )

        send_instructor_email_digest(
            h_userid=h_userid, created_before=created_before.isoformat()
        )

        digest_service.send_instructor_email_digest.assert_called_once_with(
            h_userid, created_before - timedelta(days=7), created_before
        )

    def test_it_when_TaskDone_doesnt_have_tzinfo(
        self, created_before, db_session, digest_service, h_userid, make_task_done
    ):
        created_before = created_before.replace(tzinfo=None)

        db_session.add(
            make_task_done(
                created_before=(created_before - timedelta(days=8)).isoformat()
            )
        )

        send_instructor_email_digest(
            h_userid=h_userid, created_before=created_before.isoformat()
        )

        digest_service.send_instructor_email_digest.assert_called_once_with(
            h_userid=h_userid,
            # The task adds tzinfo if it was not already present in the DB
            created_after=created_before.replace(tzinfo=timezone.utc)
            - timedelta(days=7),
            created_before=created_before,
        )

    def test_the_created_after_argument(self, created_before, digest_service, h_userid):
        created_after = datetime(
            year=2023, month=11, day=25, hour=5, tzinfo=timezone.utc
        )

        send_instructor_email_digest(
            h_userid=h_userid,
            created_before=created_before.isoformat(),
            created_after=created_after.isoformat(),
            override_to_email=sentinel.override_to_email,
        )

        assert (
            digest_service.send_instructor_email_digest.call_args[1]["created_after"]
            == created_after
        )

    def test_it_crashes_if_created_before_is_invalid(self, h_userid):
        with pytest.raises(ValueError, match="^Invalid isoformat string"):
            send_instructor_email_digest(h_userid=h_userid, created_before="invalid")

    @pytest.fixture
    def h_userid(self):
        """Return the h_userid arg that will be passed to send_instructor_email_digest()."""
        return "test_h_userid"

    @pytest.fixture
    def created_before(self):
        """Return the created_before arg that will be passed to send_instructor_email_digest()."""
        return datetime(year=2023, month=12, day=25, hour=5, tzinfo=timezone.utc)

    @pytest.fixture
    def make_task_done(self, h_userid, created_before):
        def make_task_done(omit=None, **kwargs):
            data = {
                "type": "instructor_email_digest",
                "h_userid": h_userid,
                "created_before": (created_before + timedelta(days=1)).isoformat(),
            }

            for field in omit or []:
                del data[field]

            data.update(kwargs)

            return factories.TaskDone(data=data)

        return make_task_done


@pytest.fixture(autouse=True)
def app(patch, pyramid_request):
    app = patch("lms.tasks.email_digests.app")

    @contextmanager
    def request_context():
        yield pyramid_request

    app.request_context = request_context

    return app
