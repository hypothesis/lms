from contextlib import contextmanager
from datetime import datetime
from unittest.mock import call, sentinel

import pytest
from freezegun import freeze_time

from lms.tasks.email_digests import (
    send_instructor_email_digest_tasks,
    send_instructor_email_digests,
)
from tests import factories


class TestSendInstructurEmailDigestsTasks:
    def test_it_does_nothing_if_there_are_no_instructors(
        self, send_instructor_email_digests
    ):
        send_instructor_email_digest_tasks(batch_size=42)

        send_instructor_email_digests.apply_async.assert_not_called()

    @freeze_time("2023-03-09 05:15:00")
    def test_it_sends_digests_for_instructors(
        self, send_instructor_email_digests, participating_instructors
    ):
        send_instructor_email_digest_tasks(batch_size=3)

        assert send_instructor_email_digests.apply_async.call_args_list == [
            call(
                [[user.h_userid for user in participating_instructors[:3]]],
                {
                    "updated_after": "2023-03-08T05:00:00",
                    "updated_before": "2023-03-09T05:00:00",
                },
            ),
            call(
                [[participating_instructors[-1].h_userid]],
                {
                    "updated_after": "2023-03-08T05:00:00",
                    "updated_before": "2023-03-09T05:00:00",
                },
            ),
        ]

    @pytest.mark.usefixtures("non_participating_instructor")
    def test_it_doesnt_email_non_participating_instructors(
        self, send_instructor_email_digests
    ):
        send_instructor_email_digest_tasks(batch_size=42)

        send_instructor_email_digests.apply_async.assert_not_called()

    @pytest.mark.usefixtures("non_instructor")
    def test_it_doesnt_email_non_instructors(self, send_instructor_email_digests):
        send_instructor_email_digest_tasks(batch_size=42)

        send_instructor_email_digests.apply_async.assert_not_called()

    def test_it_deduplicates_duplicate_h_userids(
        self, send_instructor_email_digests, participating_instructors, make_instructors
    ):
        # Make a user with the same h_userid as another user but
        # a different application instance.
        user = participating_instructors[0]
        instance = participating_instructors[-1].application_instance
        assert instance != user.application_instance
        duplicate_user = factories.User(
            h_userid=user.h_userid, application_instance=instance
        )
        make_instructors([duplicate_user])

        send_instructor_email_digest_tasks(batch_size=99)

        assert (
            send_instructor_email_digests.apply_async.call_args[0][0][0].count(
                duplicate_user.h_userid
            )
            == 1
        )

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

        make_instructors(users)

        return users

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
        make_instructors([user])
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

        def make_instructors(users):
            """Make the given user instructors for an assignment."""
            assignment = factories.Assignment()
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
    def send_instructor_email_digests(self, patch):
        return patch("lms.tasks.email_digests.send_instructor_email_digests")


@pytest.mark.usefixtures("digest_service")
class TestSendInstructorEmailDigests:
    def test_it(self, digest_service):
        updated_after = datetime(year=2023, month=3, day=1)
        updated_before = datetime(year=2023, month=3, day=2)

        send_instructor_email_digests(
            sentinel.h_userids,
            updated_after.isoformat(),
            updated_before.isoformat(),
            sentinel.override_to_email,
        )

        digest_service.send_emails.assert_called_once_with(
            audience=sentinel.h_userids,
            updated_after=updated_after,
            updated_before=updated_before,
            override_to_email=sentinel.override_to_email,
        )

    @pytest.mark.parametrize(
        "updated_after,updated_before",
        [
            ("invalid", "2023-02-28T00:00:00"),
            ("2023-02-28T00:00:00", "invalid"),
            ("invalid", "invalid"),
        ],
    )
    def test_it_crashes_if_updated_after_or_updated_before_is_invalid(
        self, updated_after, updated_before
    ):
        with pytest.raises(ValueError, match="^Invalid isoformat string"):
            send_instructor_email_digests(
                sentinel.h_userids, updated_after, updated_before
            )


@pytest.fixture(autouse=True)
def app(patch, pyramid_request):
    app = patch("lms.tasks.email_digests.app")

    @contextmanager
    def request_context():
        yield pyramid_request

    app.request_context = request_context

    return app
