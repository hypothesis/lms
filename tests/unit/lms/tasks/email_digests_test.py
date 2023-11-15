from contextlib import contextmanager
from datetime import datetime, timezone
from unittest.mock import call, sentinel

import celery
import pytest
from factory import post_generation
from freezegun import freeze_time
from h_matchers import Any
from sqlalchemy import delete

from lms.models import (
    AssignmentMembership,
    EmailUnsubscribe,
    Event,
    TaskDone,
    UserPreferences,
)
from lms.tasks.email_digests import (
    send_instructor_email_digest_tasks,
    send_instructor_email_digests,
)
from tests import factories


@freeze_time("2023-03-09 05:15:00")
class TestSendInstructorEmailDigestsTasks:
    def test_it_does_nothing_if_there_are_no_instructors(
        self, send_instructor_email_digests
    ):
        send_instructor_email_digest_tasks(batch_size=42)

        send_instructor_email_digests.apply_async.assert_not_called()

    def test_it_sends_digests_for_instructors(
        self, db_session, send_instructor_email_digests, InstructorFactory
    ):
        instructors = InstructorFactory.create_batch(size=4)
        db_session.add_all(
            [
                TaskDone(
                    key="task_done_0",
                    data={
                        "type": "instructor_email_digest",
                        "h_userid": instructors[0].h_userid,
                        "created_before": "2023-03-02T05:00:00",
                    },
                ),
                TaskDone(
                    key="task_done_1",
                    data={
                        "type": "instructor_email_digest",
                        "h_userid": instructors[1].h_userid,
                        "created_before": "2023-03-08T05:00:00",
                    },
                ),
                TaskDone(
                    key="task_done_2",
                    data={
                        "type": "instructor_email_digest",
                        "h_userid": instructors[2].h_userid,
                        "created_before": "2023-03-02T05:00:00",
                    },
                ),
                TaskDone(
                    key="task_done_3",
                    data={
                        "type": "instructor_email_digest",
                        "h_userid": instructors[3].h_userid,
                        "created_before": "2023-03-02T05:00:00",
                    },
                ),
            ]
        )

        send_instructor_email_digest_tasks(batch_size=2)

        expected = Any.list.containing(
            [
                call(
                    (),
                    {
                        "h_userids": Any.list.containing(
                            [instructors[0].h_userid, instructors[2].h_userid]
                        ).only(),
                        "created_after": "2023-03-02T05:00:00",
                        "created_before": "2023-03-09T05:00:00",
                    },
                ),
                call(
                    (),
                    {
                        "h_userids": [instructors[3].h_userid],
                        "created_after": "2023-03-02T05:00:00",
                        "created_before": "2023-03-09T05:00:00",
                    },
                ),
                call(
                    (),
                    {
                        "h_userids": [instructors[1].h_userid],
                        "created_after": "2023-03-08T05:00:00",
                        "created_before": "2023-03-09T05:00:00",
                    },
                ),
            ]
        ).only()
        assert send_instructor_email_digests.apply_async.call_args_list == expected

    def test_if_a_user_has_multiple_TaskDones_it_uses_the_latest_one(
        self, db_session, send_instructor_email_digests, InstructorFactory
    ):
        instructor = InstructorFactory.create()
        db_session.add_all(
            [
                TaskDone(
                    key="task_done_0",
                    data={
                        "type": "instructor_email_digest",
                        "h_userid": instructor.h_userid,
                        "created_before": "2023-03-02T05:00:00",
                    },
                ),
                TaskDone(
                    key="task_done_1",
                    data={
                        "type": "instructor_email_digest",
                        "h_userid": instructor.h_userid,
                        "created_before": "2023-03-07T05:00:00",
                    },
                ),
            ]
        )

        send_instructor_email_digest_tasks(batch_size=2)

        assert send_instructor_email_digests.apply_async.call_args_list == [
            call(
                (),
                {
                    "h_userids": [instructor.h_userid],
                    "created_after": "2023-03-07T05:00:00",
                    "created_before": "2023-03-09T05:00:00",
                },
            ),
        ]

    def test_if_a_user_has_no_TaskDones(
        self, send_instructor_email_digests, InstructorFactory
    ):
        instructor = InstructorFactory.create()

        send_instructor_email_digest_tasks(batch_size=2)

        assert send_instructor_email_digests.apply_async.call_args_list == [
            call(
                (),
                {
                    "h_userids": [instructor.h_userid],
                    "created_after": "2023-03-02T05:00:00",
                    "created_before": "2023-03-09T05:00:00",
                },
            ),
        ]

    def test_if_there_are_invalid_TaskDones(
        self,
        db_session,
        send_instructor_email_digests,
        InstructorFactory,
    ):
        instructor = InstructorFactory.create()
        db_session.add_all(
            [
                TaskDone(
                    key="task_done_0",
                    data={
                        "type": "instructor_email_digest",
                        "h_userid": instructor.h_userid,
                        # No "created_before".
                    },
                ),
                TaskDone(
                    key="task_done_1",
                    data={},
                ),
                TaskDone(
                    key="task_done_2",
                    data=None,
                ),
            ]
        )

        send_instructor_email_digest_tasks(batch_size=2)

        assert send_instructor_email_digests.apply_async.call_args_list == [
            call(
                (),
                {
                    "h_userids": [instructor.h_userid],
                    "created_after": "2023-03-02T05:00:00",
                    "created_before": "2023-03-09T05:00:00",
                },
            ),
        ]

    def test_it_doesnt_email_for_courses_with_no_launches(
        self, db_session, send_instructor_email_digests, InstructorFactory
    ):
        InstructorFactory()
        db_session.execute(delete(Event))

        send_instructor_email_digest_tasks(batch_size=42)

        send_instructor_email_digests.apply_async.assert_not_called()

    def test_it_doesnt_email_non_participating_instructors(
        self, send_instructor_email_digests, InstructorFactory
    ):
        instructor = InstructorFactory()
        instructor.application_instance.settings.set(
            "hypothesis", "instructor_email_digests_enabled", False
        )

        send_instructor_email_digest_tasks(batch_size=42)

        send_instructor_email_digests.apply_async.assert_not_called()

    def test_it_doesnt_email_non_instructors(
        self, db_session, send_instructor_email_digests, InstructorFactory
    ):
        InstructorFactory()
        db_session.execute(delete(AssignmentMembership))

        send_instructor_email_digest_tasks(batch_size=42)

        send_instructor_email_digests.apply_async.assert_not_called()

    def test_it_doesnt_email_unsubscribed_instructors(
        self, send_instructor_email_digests, InstructorFactory
    ):
        instructor = InstructorFactory()
        factories.EmailUnsubscribe(
            h_userid=instructor.h_userid, tag=EmailUnsubscribe.Tag.INSTRUCTOR_DIGEST
        )

        send_instructor_email_digest_tasks(batch_size=42)

        assert send_instructor_email_digests.apply_async.call_args_list == []

    def test_it_doesnt_email_instructors_who_dont_get_emails_on_this_day(
        self, db_session, send_instructor_email_digests, InstructorFactory
    ):
        instructor = InstructorFactory()
        db_session.add(
            UserPreferences(
                h_userid=instructor.h_userid,
                preferences={
                    "instructor_email_digest": {
                        datetime.now(timezone.utc).strftime("%A").lower(): False,
                    }
                },
            )
        )

        send_instructor_email_digest_tasks(batch_size=42)

        send_instructor_email_digests.apply_async.assert_not_called()

    def test_it_deduplicates_duplicate_h_userids(
        self, send_instructor_email_digests, InstructorFactory
    ):
        instructor = InstructorFactory()
        duplicate_instructor = InstructorFactory(h_userid=instructor.h_userid)

        send_instructor_email_digest_tasks(batch_size=99)

        assert (
            send_instructor_email_digests.apply_async.call_args[0][1][
                "h_userids"
            ].count(duplicate_instructor.h_userid)
            == 1
        )

    @pytest.fixture(autouse=True)
    def retry(self, patch):
        return patch(
            "lms.tasks.email_digests.send_instructor_email_digest_tasks.retry",
            side_effect=celery.exceptions.Retry,
        )

    @pytest.fixture(autouse=True)
    def send_instructor_email_digests(self, patch):
        return patch("lms.tasks.email_digests.send_instructor_email_digests")

    @pytest.fixture
    def instructor_role(self):
        return factories.LTIRole(value="Instructor")

    @pytest.fixture
    def InstructorFactory(self, db_session, instructor_role):
        class InstructorFactory(factories.User):
            class Meta:
                sqlalchemy_session = db_session

            @post_generation
            def make_user_into_participating_instructor(
                obj, _create, _extracted, **_kwargs
            ):  # pylint:disable=no-self-argument
                obj.application_instance.settings.set(
                    "hypothesis", "instructor_email_digests_enabled", True
                )
                course = factories.Course(application_instance=obj.application_instance)
                assignment = factories.Assignment()
                factories.AssignmentGrouping(grouping=course, assignment=assignment)
                factories.AssignmentMembership(
                    assignment=assignment, user=obj, lti_role=instructor_role
                )
                factories.Event(
                    timestamp=datetime(2023, 3, 8, 22),
                    application_instance=obj.application_instance,
                    course=course,
                    assignment=assignment,
                )

        return InstructorFactory


@pytest.mark.usefixtures("digest_service")
class TestSendInstructorEmailDigests:
    def test_it(self, digest_service):
        created_after = datetime(year=2023, month=3, day=1)
        created_before = datetime(year=2023, month=3, day=2)

        send_instructor_email_digests(
            h_userids=sentinel.h_userids,
            created_after=created_after.isoformat(),
            created_before=created_before.isoformat(),
            override_to_email=sentinel.override_to_email,
        )

        digest_service.send_instructor_email_digests.assert_called_once_with(
            sentinel.h_userids,
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
            send_instructor_email_digests(
                h_userids=sentinel.h_userids,
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
