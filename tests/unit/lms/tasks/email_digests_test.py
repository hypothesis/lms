import logging
from contextlib import contextmanager
from datetime import datetime
from unittest.mock import Mock, call, sentinel

import celery
import pytest
from freezegun import freeze_time
from h_matchers import Any

from lms.models import EmailUnsubscribe
from lms.services.digest import SendDigestsError
from lms.services.mailchimp import MailchimpError
from lms.tasks.email_digests import (
    send_instructor_email_digest_tasks,
    send_instructor_email_digests,
)
from tests import factories


class TestSendInstructurEmailDigestsTasks:
    def test_it_does_nothing_if_there_are_no_instructors(
        self, send_instructor_email_digests
    ):
        send_instructor_email_digest_tasks(  # pylint:disable=no-value-for-parameter
            batch_size=42
        )

        send_instructor_email_digests.apply_async.assert_not_called()

    @freeze_time("2023-03-09 05:15:00")
    def test_it_sends_digests_for_instructors(
        self, send_instructor_email_digests, participating_instructors
    ):
        send_instructor_email_digest_tasks(  # pylint:disable=no-value-for-parameter
            batch_size=3
        )

        assert send_instructor_email_digests.apply_async.call_args_list == [
            call(
                (),
                {
                    "h_userids": [
                        user.h_userid for user in participating_instructors[:3]
                    ],
                    "updated_after": "2023-03-08T05:00:00",
                    "updated_before": "2023-03-09T05:00:00",
                },
            ),
            call(
                (),
                {
                    "h_userids": [participating_instructors[-1].h_userid],
                    "updated_after": "2023-03-08T05:00:00",
                    "updated_before": "2023-03-09T05:00:00",
                },
            ),
        ]

    def test_it_retries_if_the_db_query_raises(
        self, retry, caplog, report_exception, pyramid_request
    ):
        pyramid_request.db = Mock(spec_set=["scalars"])
        exception = RuntimeError("The DB crashed!")
        pyramid_request.db.scalars.side_effect = exception

        with pytest.raises(celery.exceptions.Retry):
            send_instructor_email_digest_tasks(  # pylint:disable=no-value-for-parameter
                batch_size=42
            )

        assert caplog.record_tuples == [
            ("lms.tasks.email_digests", logging.ERROR, "The DB crashed!")
        ]
        report_exception.assert_called_once_with(exception)
        retry.assert_called_once_with(countdown=Any.int())

    def test_it_retries_if_celery_raises(
        self,
        send_instructor_email_digests,
        participating_instructors,
        caplog,
        report_exception,
        retry,
    ):
        exception = RuntimeError("Celery crashed!")
        # Make scheduling the first batch fail but the second succeed.
        send_instructor_email_digests.apply_async.side_effect = [exception, None]

        with pytest.raises(celery.exceptions.Retry):
            send_instructor_email_digest_tasks(  # pylint:disable=no-value-for-parameter
                batch_size=2
            )

        # The batches of h_userids that send_instructor_email_digests() was called with.
        batches = [
            call[0][1]["h_userids"]
            for call in send_instructor_email_digests.apply_async.call_args_list
        ]
        # It should have loggged the exception when scheduling the first batch failed.
        assert caplog.record_tuples == [
            ("lms.tasks.email_digests", logging.ERROR, "Celery crashed!")
        ]
        # It should have reported the exception to Sentry.
        report_exception.assert_called_once_with(exception)
        # After scheduling the first batch failed it should have continued and
        # tried to schedule the second batch anyway, so it should have tried to
        # schedule all the h_userids.
        assert set(h_userid for batch in batches for h_userid in batch) == set(
            participating_instructor.h_userid
            for participating_instructor in participating_instructors
        )
        # It should have scheduled a retry of the failed batch.
        retry.assert_called_once_with(
            kwargs={
                "batch_size": 2,
                "h_userids": batches[0],
            },
            countdown=Any.int(),
        )

    def test_it_uses_the_given_h_userids(self, send_instructor_email_digests):
        # The method accepts an optional h_userids argument that will be used
        # instead of retrieving the h_userids from the DB.
        # This is used when the task schedules a retry of itself with only the
        # h_userids that it failed to schedule.
        h_userids = [sentinel.h_userid_1, sentinel.h_userid_2]

        send_instructor_email_digest_tasks(  # pylint:disable=no-value-for-parameter
            batch_size=2, h_userids=h_userids
        )

        send_instructor_email_digests.apply_async.assert_called_once_with(
            (), Any.dict.containing({"h_userids": h_userids})
        )

    @pytest.mark.usefixtures("non_participating_instructor")
    def test_it_doesnt_email_non_participating_instructors(
        self, send_instructor_email_digests
    ):
        send_instructor_email_digest_tasks(  # pylint:disable=no-value-for-parameter
            batch_size=42
        )

        send_instructor_email_digests.apply_async.assert_not_called()

    @pytest.mark.usefixtures("non_instructor")
    def test_it_doesnt_email_non_instructors(self, send_instructor_email_digests):
        send_instructor_email_digest_tasks(  # pylint:disable=no-value-for-parameter
            batch_size=42
        )

        send_instructor_email_digests.apply_async.assert_not_called()

    def test_it_doesnt_email_unsubscribed_instructors(
        self, send_instructor_email_digests, unsubscribed_instructors
    ):
        send_instructor_email_digest_tasks(  # pylint:disable=no-value-for-parameter
            batch_size=42
        )

        assert send_instructor_email_digests.apply_async.call_args_list == [
            call(
                (),
                Any.dict.containing(
                    {"h_userids": [unsubscribed_instructors[0].h_userid]}
                ),
            )
        ]

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

        send_instructor_email_digest_tasks(  # pylint:disable=no-value-for-parameter
            batch_size=99
        )

        assert (
            send_instructor_email_digests.apply_async.call_args[0][1][
                "h_userids"
            ].count(duplicate_user.h_userid)
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
    def unsubscribed_instructors(self, participating_instructors):
        # We leave the first instructor alone, no unsubcribes

        for instructor in participating_instructors[1:]:
            # We unsubcribe the rest
            factories.EmailUnsubscribe(
                h_userid=instructor.h_userid,
                tag=EmailUnsubscribe.Tag.INSTRUCTOR_DIGEST,
            )

        return participating_instructors

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
    def retry(self, patch):
        return patch(
            "lms.tasks.email_digests.send_instructor_email_digest_tasks.retry",
            side_effect=celery.exceptions.Retry,
        )

    @pytest.fixture(autouse=True)
    def send_instructor_email_digests(self, patch):
        return patch("lms.tasks.email_digests.send_instructor_email_digests")


@pytest.mark.usefixtures("digest_service")
class TestSendInstructorEmailDigests:
    def test_it(self, digest_service):
        updated_after = datetime(year=2023, month=3, day=1)
        updated_before = datetime(year=2023, month=3, day=2)

        send_instructor_email_digests(  # pylint:disable=no-value-for-parameter
            h_userids=sentinel.h_userids,
            updated_after=updated_after.isoformat(),
            updated_before=updated_before.isoformat(),
            override_to_email=sentinel.override_to_email,
        )

        digest_service.send_instructor_email_digests.assert_called_once_with(
            sentinel.h_userids,
            updated_after,
            updated_before,
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
            send_instructor_email_digests(  # pylint:disable=no-value-for-parameter
                h_userids=sentinel.h_userids,
                updated_after=updated_after,
                updated_before=updated_before,
            )

    def test_it_retries_if_sending_fails(self, digest_service, retry):
        updated_after = datetime(year=2023, month=3, day=1)
        updated_before = datetime(year=2023, month=3, day=2)
        # send_instructor_email_digests() raises a SendDigestsError whose
        # errors attribute is a dict mapping the h_userid's that failed to send
        # to their corresponding MailchimpError's.
        digest_service.send_instructor_email_digests.side_effect = SendDigestsError(
            errors={
                sentinel.failed_h_userid_1: MailchimpError(),
                sentinel.failed_h_userid_2: MailchimpError(),
            }
        )

        send_instructor_email_digests(  # pylint:disable=no-value-for-parameter
            h_userids=sentinel.h_userids,
            updated_after=updated_after.isoformat(),
            updated_before=updated_before.isoformat(),
            override_to_email=sentinel.override_to_email,
        )

        # It retries the task with the same arguments except that h_userids is
        # now only those userids that failed to send.
        retry.assert_called_once_with(
            kwargs={
                "h_userids": Any.list.containing(
                    [sentinel.failed_h_userid_1, sentinel.failed_h_userid_2]
                ).only(),
                "updated_after": updated_after.isoformat(),
                "updated_before": updated_before.isoformat(),
                "override_to_email": sentinel.override_to_email,
            },
            countdown=Any.int(),
        )

    def test_it_retries_if_sending_fails_with_an_unexpected_exception(
        self, caplog, digest_service, report_exception, retry
    ):
        exception = RuntimeError("Unexpected")
        digest_service.send_instructor_email_digests.side_effect = exception

        send_instructor_email_digests(  # pylint:disable=no-value-for-parameter
            h_userids=sentinel.h_userids,
            updated_after="2023-02-27T00:00:00",
            updated_before="2023-02-28T00:00:00",
            override_to_email=sentinel.override_to_email,
        )

        assert caplog.record_tuples == [
            ("lms.tasks.email_digests", logging.ERROR, "Unexpected")
        ]
        report_exception.assert_called_once_with(exception)
        retry.assert_called_once_with(countdown=Any.int())

    @pytest.fixture
    def retry(self, patch):
        return patch("lms.tasks.email_digests.send_instructor_email_digests.retry")


@pytest.fixture(autouse=True)
def app(patch, pyramid_request):
    app = patch("lms.tasks.email_digests.app")

    @contextmanager
    def request_context():
        yield pyramid_request

    app.request_context = request_context

    return app


@pytest.fixture(autouse=True)
def report_exception(patch):
    return patch("lms.tasks.email_digests.report_exception")
