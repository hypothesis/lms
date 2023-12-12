from dataclasses import asdict
from datetime import datetime
from unittest.mock import sentinel

import factory
import pytest
from freezegun import freeze_time
from h_matchers import Any

from lms.services.digest import (
    Annotation,
    AssignmentInfo,
    CourseInfo,
    DigestContext,
    DigestService,
    UserInfo,
    service_factory,
)
from lms.services.mailchimp import EmailRecipient, EmailSender
from tests import factories


class TestDigestService:
    @freeze_time("2023-04-30")
    def test_send_instructor_email_digest(
        self,
        svc,
        h_api,
        context,
        DigestContext,
        db_session,
        send,
        sender,
        email_preferences_service,
        created_before,
    ):
        context.user_info = UserInfoFactory()
        context.instructor_digest.return_value = {"total_annotations": 1}

        svc.send_instructor_email_digest(
            sentinel.h_userid, sentinel.created_after, created_before
        )

        h_api.get_annotations.assert_called_once_with(
            sentinel.h_userid, sentinel.created_after, created_before
        )
        DigestContext.assert_called_once_with(
            db_session,
            sentinel.h_userid,
            [
                Annotation(
                    userid=annotation_dict["author"]["userid"],
                    authority_provided_id=annotation_dict["group"][
                        "authority_provided_id"
                    ],
                    guid=annotation_dict["metadata"]["lms"]["guid"],
                    resource_link_id=annotation_dict["metadata"]["lms"]["assignment"][
                        "resource_link_id"
                    ],
                )
                for annotation_dict in h_api.get_annotations.return_value
            ],
        )
        context.instructor_digest.assert_called_once_with(context.user_info.h_userid)
        email_preferences_service.preferences_url.assert_called_once_with(
            context.user_info.h_userid, "instructor_digest"
        )
        assert (
            context.instructor_digest.return_value["preferences_url"]
            == email_preferences_service.preferences_url.return_value
        )
        send.delay.assert_called_once_with(
            task_done_key=f"instructor_email_digest::{context.user_info.h_userid}::2023-04-30",
            task_done_data={
                "type": "instructor_email_digest",
                "h_userid": context.user_info.h_userid,
                "created_before": created_before.isoformat(),
            },
            template="lms:templates/email/instructor_email_digest/",
            sender=asdict(sender),
            recipient=asdict(
                EmailRecipient(context.user_info.email, context.user_info.display_name)
            ),
            template_vars=context.instructor_digest.return_value,
            unsubscribe_url=email_preferences_service.unsubscribe_url.return_value,
        )

    def test_send_instructor_email_digest_without_deduplication(
        self, svc, context, send, created_before
    ):
        context.user_info = UserInfoFactory()
        context.instructor_digest.side_effect = [{"total_annotations": 1}]

        svc.send_instructor_email_digest(
            sentinel.h_userid,
            sentinel.created_after,
            created_before,
            deduplicate=False,
        )

        # If deduplicate=True is passed to DigestService then it passes
        # task_done_key=None to send() which disables deduplication of
        # sent emails. This is used by admin pages that actually want to allow
        # you to send duplicate emails if requested.
        assert not send.delay.call_args.kwargs["task_done_key"]
        assert not send.delay.call_args.kwargs["task_done_data"]

    def test_send_instructor_email_digest_doesnt_send_empty_digests(
        self, svc, context, send, created_before
    ):
        context.user_info = UserInfoFactory()
        context.instructor_digest.return_value = {"total_annotations": 0}

        svc.send_instructor_email_digest(
            sentinel.h_userid, sentinel.created_after, created_before
        )

        send.delay.assert_not_called()

    def test_send_instructor_email_digest_ignores_instructors_with_no_email_address(
        self, svc, context, send, created_before
    ):
        context.user_info = UserInfoFactory(email=None)
        context.instructor_digest.return_value = {"total_annotations": 1}

        svc.send_instructor_email_digest(
            sentinel.h_userid, sentinel.created_after, created_before
        )

        send.delay.assert_not_called()

    @pytest.mark.usefixtures("email_preferences_service")
    def test_send_instructor_email_digest_uses_override_to_email(
        self, svc, context, send, created_before
    ):
        context.user_info = UserInfoFactory()
        context.instructor_digest.return_value = {"total_annotations": 1}

        svc.send_instructor_email_digest(
            sentinel.h_userid,
            sentinel.created_after,
            created_before,
            override_to_email=sentinel.override_to_email,
        )

        assert (
            send.delay.call_args[1]["recipient"]["email"] == sentinel.override_to_email
        )

    def test_send_instructor_email_digest_handles_annotations_with_no_metadata(
        self, svc, h_api, DigestContext, created_before
    ):
        for annotation_dict in h_api.get_annotations.return_value:
            del annotation_dict["metadata"]["lms"]

        svc.send_instructor_email_digest(
            [sentinel.h_userid], sentinel.created_after, created_before
        )

        assert DigestContext.call_args[0][2] == [
            Annotation(
                userid=annotation_dict["author"]["userid"],
                authority_provided_id=annotation_dict["group"]["authority_provided_id"],
                guid=None,
                resource_link_id=None,
            )
            for annotation_dict in h_api.get_annotations.return_value
        ]

    @pytest.fixture
    def created_before(self):
        return datetime.fromisoformat("2023-11-23T15:48:31.834581+00:00")

    @pytest.fixture(autouse=True)
    def DigestContext(self, patch):
        return patch("lms.services.digest.DigestContext")

    @pytest.fixture
    def context(self, DigestContext):
        return DigestContext.return_value

    @pytest.fixture
    def sender(self):
        return EmailSender(sentinel.subaccount, sentinel.from_email, sentinel.from_name)

    @pytest.fixture
    def h_api(self, h_api):
        def asdict(annotation):
            """Return the given Annotation in the h bulk annotation API's dict format."""
            return {
                "author": {
                    "userid": annotation.userid,
                },
                "group": {
                    "authority_provided_id": annotation.authority_provided_id,
                },
                "metadata": {
                    "lms": {
                        "guid": annotation.guid,
                        "assignment": {
                            "resource_link_id": annotation.resource_link_id,
                        },
                    },
                },
            }

        h_api.get_annotations.return_value = [
            asdict(AnnotationFactory()),
            asdict(AnnotationFactory()),
        ]

        return h_api

    @pytest.fixture
    def svc(self, db_session, h_api, sender, email_preferences_service):
        return DigestService(
            db=db_session,
            h_api=h_api,
            sender=sender,
            email_preferences_service=email_preferences_service,
        )


class TestDigestContext:
    def test_instructor_digest(self, db_session, make_instructor):
        courses = factories.Course.create_batch(2)
        instructor, learner_1, learner_2 = factories.User.create_batch(3)
        for course in courses:
            make_instructor(instructor, course)
        annotations = [
            AnnotationFactory(
                authority_provided_id=courses[0].authority_provided_id,
                userid=learner_1.h_userid,
            ),
            AnnotationFactory(
                authority_provided_id=courses[0].authority_provided_id,
                userid=learner_2.h_userid,
            ),
            AnnotationFactory(
                authority_provided_id=courses[1].authority_provided_id,
                userid=learner_1.h_userid,
            ),
            AnnotationFactory(
                authority_provided_id=courses[1].authority_provided_id,
                userid=learner_1.h_userid,
            ),
        ]
        assignment = factories.Assignment(
            title="Test Assignment Title",
            tool_consumer_instance_guid=annotations[0].guid,
            resource_link_id=annotations[0].resource_link_id,
        )
        context = DigestContext(db_session, [instructor.h_userid], annotations)
        factories.AssignmentGrouping(assignment=assignment, grouping=courses[0])

        digest = context.instructor_digest(instructor.h_userid)

        assert digest == {
            "total_annotations": 4,
            "annotators": Any.list.containing(
                [learner_1.h_userid, learner_2.h_userid]
            ).only(),
            "courses": Any.list.containing(
                [
                    {
                        "title": courses[0].lms_name,
                        "annotators": Any.list.containing(
                            [learner_1.h_userid, learner_2.h_userid]
                        ).only(),
                        "num_annotations": 2,
                        "assignments": [
                            {
                                "annotators": [learner_1.h_userid],
                                "num_annotations": 1,
                                "title": assignment.title,
                            }
                        ],
                    },
                    {
                        "title": courses[1].lms_name,
                        "annotators": [learner_1.h_userid],
                        "num_annotations": 2,
                        "assignments": [],
                    },
                ]
            ).only(),
        }

    def test_instructor_digest_removes_courses_with_no_learner_annotations(
        self, db_session, make_instructor
    ):
        course = factories.Course()
        instructor = factories.User()
        make_instructor(instructor, course)
        annotations = [
            AnnotationFactory(
                authority_provided_id=course.authority_provided_id,
                userid=instructor.h_userid,
            )
        ]
        context = DigestContext(db_session, [instructor.h_userid], annotations)

        digest = context.instructor_digest(instructor.h_userid)

        assert digest == {"total_annotations": 0, "annotators": [], "courses": []}

    def test_instructor_digest_omits_courses_where_the_user_isnt_an_instructor(
        self, db_session, make_instructor
    ):
        course, other_course = factories.Course.create_batch(2)
        instructor, learner = factories.User.create_batch(2)
        make_instructor(instructor, other_course)
        annotations = [
            AnnotationFactory(
                authority_provided_id=course.authority_provided_id,
                userid=learner.h_userid,
            )
        ]
        context = DigestContext(db_session, [instructor.h_userid], annotations)

        digest = context.instructor_digest(instructor.h_userid)

        assert digest == {"total_annotations": 0, "annotators": [], "courses": []}

    def test_assignment_infos(self, db_session):
        annotations = AnnotationFactory.create_batch(size=2)
        assignments = [
            factories.Assignment(
                tool_consumer_instance_guid=annotation.guid,
                resource_link_id=annotation.resource_link_id,
            )
            for annotation in annotations
        ]
        courses = factories.Course.create_batch(size=2)
        for assignment, course in zip(assignments, courses):
            factories.AssignmentGrouping(assignment=assignment, grouping=course)
        context = DigestContext(db_session, sentinel.h_userid, annotations)

        assignment_infos = context.assignment_infos

        assert sorted(assignment_infos) == sorted(
            [
                AssignmentInfo(
                    assignment.id,
                    assignment.tool_consumer_instance_guid,
                    assignment.resource_link_id,
                    assignment.title,
                    course.authority_provided_id,
                )
                for assignment, course in zip(assignments, courses)
            ]
        )

    def test_assignment_infos_when_an_annotation_has_no_matching_assignment(
        self, db_session
    ):
        context = DigestContext(db_session, sentinel.h_userid, [AnnotationFactory()])

        assignment_infos = context.assignment_infos

        assert assignment_infos == []

    @pytest.mark.parametrize("title", [None, "", " "])
    def test_assignment_infos_doesnt_return_assignments_with_no_titles(
        self, db_session, title
    ):
        annotation = AnnotationFactory()
        assignment = factories.Assignment(
            tool_consumer_instance_guid=annotation.guid,
            resource_link_id=annotation.resource_link_id,
            title=title,
        )
        course = factories.Course()
        factories.AssignmentGrouping(assignment=assignment, grouping=course)
        context = DigestContext(db_session, sentinel.h_userid, [annotation])

        assignment_infos = context.assignment_infos

        assert assignment_infos == []

    def test_user_info(self, db_session):
        user = factories.User()
        context = DigestContext(db_session, user.h_userid, [])

        user_info = context.user_info

        assert user_info == UserInfo(
            h_userid=user.h_userid, email=Any(), display_name=Any()
        )
        assert context.user_info is user_info

    def test_user_info_ignores_duplicate_userids(self, db_session):
        user = factories.User()
        context = DigestContext(
            db_session,
            user.h_userid,
            AnnotationFactory.create_batch(2, userid=user.h_userid),
        )

        user_info = context.user_info

        assert user_info == UserInfo(
            h_userid=user.h_userid, email=Any(), display_name=Any()
        )

    @pytest.mark.parametrize(
        "users,expected_email",
        [
            # It uses the most recent email.
            (
                [
                    factories.User.build(
                        h_userid="id",
                        email="email@example.com",
                        updated=datetime(year=2024, month=1, day=2),
                    ),
                    factories.User.build(
                        h_userid="id",
                        email="older@example.com",
                        updated=datetime(year=2024, month=1, day=1),
                    ),
                ],
                "email@example.com",
            ),
            # It uses None if we have no email for the user.
            (
                [factories.User.build(h_userid="id", email=None)],
                None,
            ),
            # If the most recent user has no email it falls back to an older one.
            (
                [
                    factories.User.build(
                        h_userid="id",
                        email=None,
                        updated=datetime(year=2024, month=1, day=2),
                    ),
                    factories.User.build(
                        h_userid="id",
                        email="email@example.com",
                        updated=datetime(year=2024, month=1, day=1),
                    ),
                ],
                "email@example.com",
            ),
        ],
    )
    def test_user_info_email(self, db_session, users, expected_email):
        db_session.add_all(users)

        context = DigestContext(db_session, "id", [])

        assert context.user_info == Any.instance_of(UserInfo).with_attrs(
            {"h_userid": "id", "email": expected_email}
        )

    @pytest.mark.parametrize(
        "users,expected_display_name",
        [
            # It uses the most recent display name.
            (
                [
                    factories.User.build(
                        h_userid="id",
                        display_name="most_recent",
                        updated=datetime(year=2024, month=1, day=2),
                    ),
                    factories.User.build(
                        h_userid="id",
                        display_name="older",
                        updated=datetime(year=2024, month=1, day=1),
                    ),
                ],
                "most_recent",
            ),
            # It uses None if we have no display name for the user.
            (
                [factories.User.build(h_userid="id", display_name=None)],
                None,
            ),
            # If the most recent user has no display name it falls back to an older one.
            (
                [
                    factories.User.build(
                        h_userid="id",
                        display_name=None,
                        updated=datetime(year=2024, month=1, day=2),
                    ),
                    factories.User.build(
                        h_userid="id",
                        display_name="display_name",
                        updated=datetime(year=2024, month=1, day=1),
                    ),
                ],
                "display_name",
            ),
        ],
    )
    def test_user_info_display_name(self, db_session, users, expected_display_name):
        db_session.add_all(users)

        context = DigestContext(db_session, "id", [])

        assert context.user_info == Any.instance_of(UserInfo).with_attrs(
            {"h_userid": "id", "display_name": expected_display_name}
        )

    def test_course_infos(self, db_session, make_instructor, make_learner):
        course = factories.Course()
        instructors = factories.User.create_batch(2)
        for instructor in instructors:
            make_instructor(instructor, course)
        learner = factories.User()
        make_learner(learner, course)
        section = factories.CanvasSection(parent=course)
        annotations = [
            AnnotationFactory(
                authority_provided_id=grouping.authority_provided_id,
                userid=learner.h_userid,
            )
            for grouping in (course, course, section, section)
        ]
        context = DigestContext(
            db_session, [instructor.h_userid for instructor in instructors], annotations
        )

        course_infos = context.course_infos

        assert course_infos == [
            Any.instance_of(CourseInfo).with_attrs(
                {
                    "authority_provided_id": course.authority_provided_id,
                    "instructor_h_userids": Any.tuple.containing(
                        [instructor.h_userid for instructor in instructors]
                    ).only(),
                    "learner_annotations": Any.tuple.containing(annotations).only(),
                }
            )
        ]
        assert context.course_infos is course_infos

    def test_course_infos_with_multiple_groupings(self, db_session):
        instances = factories.ApplicationInstance.create_batch(2)
        # Two courses with the same authority_provided_id but different instances.
        courses = [
            factories.Course.create(
                authority_provided_id="course_id", application_instance=instance
            )
            for instance in instances
        ]
        sub_groupings = [
            # Two sub-groups with different authority_provided_id's belonging
            # to the same instance and course. (This happens for example when a
            # Canvas course has two sections.)
            *factories.CanvasSection.create_batch(
                2,
                application_instance=courses[0].application_instance,
                parent=courses[0],
            ),
            # Two sub-groups with the same authority_provided_id but different
            # instances, and belonging to courses that have the same course
            # authority_provided_id but different instances. (This happens for
            # example when a Canvas instance has two application instances both
            # used in groups assignments in the same course.)
            *[
                factories.CanvasGroup(
                    authority_provided_id="subgroup_id",
                    application_instance=course.application_instance,
                    parent=course,
                )
                for course in courses
            ],
        ]
        annotations = [
            AnnotationFactory(authority_provided_id=grouping.authority_provided_id)
            for grouping in courses + sub_groupings
        ]
        context = DigestContext(db_session, [], annotations)

        assert context.course_infos == [
            Any.instance_of(CourseInfo).with_attrs(
                {
                    "authority_provided_id": "course_id",
                    "learner_annotations": Any.tuple.of_size(6),
                }
            )
        ]

    def test_course_infos_with_no_annotations(self, db_session):
        context = DigestContext(db_session, [], [])

        assert context.course_infos == []

    def test_course_infos_title(self, db_session):
        courses = [
            factories.Course.build(
                authority_provided_id="id",
                lms_name="most_recent",
                updated=datetime(year=2024, month=1, day=2),
            ),
            factories.Course.build(
                authority_provided_id="id",
                lms_name="older",
                updated=datetime(year=2024, month=1, day=1),
            ),
        ]
        db_session.add_all(courses)
        context = DigestContext(
            db_session,
            [],
            [
                AnnotationFactory(authority_provided_id=course.authority_provided_id)
                for course in courses
            ],
        )

        assert context.course_infos == Any.list.containing(
            [
                Any.instance_of(CourseInfo).with_attrs(
                    {
                        "authority_provided_id": "id",
                        "title": "most_recent",
                    }
                )
            ]
        )

    def test_course_infos_doesnt_count_learners(self, db_session, make_learner):
        course = factories.Course()
        learner = factories.User()
        make_learner(learner, course)
        annotation = AnnotationFactory(
            authority_provided_id=course.authority_provided_id, userid=learner.h_userid
        )
        context = DigestContext(db_session, [], [annotation])

        assert context.course_infos == [
            Any.instance_of(CourseInfo).with_attrs({"instructor_h_userids": ()})
        ]

    def test_course_infos_doesnt_count_instructor_annotations(
        self, db_session, make_instructor
    ):
        course = factories.Course()
        instructor = factories.User()
        make_instructor(instructor, course)
        annotation = AnnotationFactory(
            authority_provided_id=course.authority_provided_id,
            userid=instructor.h_userid,
        )
        context = DigestContext(db_session, [], [annotation])

        assert context.course_infos == [
            Any.instance_of(CourseInfo).with_attrs({"learner_annotations": ()})
        ]

    def test_course_infos_doesnt_count_instructors_from_other_courses(
        self, db_session, make_instructor
    ):
        course, other_course = factories.Course.create_batch(2)
        user = factories.User()
        # `user` is an instructor in `other_course`.
        make_instructor(user, other_course)
        # `user` is a learner in `course` and has created an annotation.
        annotation = AnnotationFactory(
            authority_provided_id=course.authority_provided_id,
            userid=user.h_userid,
        )
        context = DigestContext(db_session, [], [annotation])

        assert context.course_infos == [
            Any.instance_of(CourseInfo).with_attrs(
                {"instructor_h_userids": (), "learner_annotations": (annotation,)}
            )
        ]

    def test_course_infos_doesnt_count_annotations_from_other_courses(self, db_session):
        course, other_course = factories.Course.create_batch(2)
        course_annotation = AnnotationFactory(
            authority_provided_id=course.authority_provided_id
        )
        other_course_annotation = AnnotationFactory(
            authority_provided_id=other_course.authority_provided_id
        )
        context = DigestContext(
            db_session, [], [course_annotation, other_course_annotation]
        )

        assert context.course_infos == Any.list.containing(
            [
                Any.instance_of(CourseInfo).with_attrs(
                    {"learner_annotations": (course_annotation,)}
                )
            ]
        )

    def test_course_infos_ignores_unknown_authority_provided_ids(self, db_session):
        context = DigestContext(
            db_session, [], [AnnotationFactory(authority_provided_id="unknown")]
        )

        assert context.course_infos == []


class TestServiceFactory:
    def test_it(self, pyramid_request, h_api, DigestService, email_preferences_service):
        settings = pyramid_request.registry.settings
        settings["mailchimp_digests_subaccount"] = sentinel.digests_subaccount
        settings["mailchimp_digests_email"] = sentinel.digests_from_email
        settings["mailchimp_digests_name"] = sentinel.digests_from_name

        service = service_factory(sentinel.context, pyramid_request)

        DigestService.assert_called_once_with(
            db=pyramid_request.db,
            h_api=h_api,
            sender=EmailSender(
                sentinel.digests_subaccount,
                sentinel.digests_from_email,
                sentinel.digests_from_name,
            ),
            email_preferences_service=email_preferences_service,
        )
        assert service == DigestService.return_value

    @pytest.fixture
    def DigestService(self, patch):
        return patch("lms.services.digest.DigestService")


class AnnotationFactory(factory.Factory):
    """
    A factory for annotation dicts.

    >>> Annotation()
    {'author': {'userid': 'acct:user_1@lms.hypothes.is'}, 'group': ...}
    >>> Annotation(userid='acct:custom_username@lms.hypothes.is')
    {'author': {'userid': 'acct:custom_username@lms.hypothes.is'}, 'group': ...}
    >>> Annotation(authority_provided_id='custom_id')
    {'author': {'userid': 'acct:user_2@lms.hypothes.is'}, 'group': ...}
    """

    class Meta:
        model = Annotation

    userid = factory.Sequence(lambda n: f"acct:user_{n}@lms.hypothes.is")
    authority_provided_id = factory.Sequence(lambda n: f"group_{n}")
    guid = factory.Sequence(lambda n: f"guid_{n}")
    resource_link_id = factory.Sequence(lambda n: f"resource_link_id{n}")


class UserInfoFactory(factory.Factory):
    class Meta:
        model = UserInfo

    h_userid = factory.Sequence(lambda n: f"acct:user_{n}@lms.hypothes.is")
    email = factory.Sequence(lambda n: f"user_{n}@example.com")
    display_name = factory.Sequence(lambda n: f"User {n}")


@pytest.fixture
def instructor_role():
    return factories.LTIRole(value="Instructor")


@pytest.fixture
def learner_role():
    return factories.LTIRole(value="Learner")


@pytest.fixture
def make_instructor(db_session, instructor_role):
    def make_instructor(user, course):
        """Make each user in `users` an instructor in `course`."""
        assignment = factories.Assignment()
        factories.AssignmentGrouping(assignment=assignment, grouping=course)
        factories.AssignmentMembership(
            assignment=assignment, user=user, lti_role=instructor_role
        )
        db_session.flush()

    return make_instructor


@pytest.fixture
def make_learner(db_session, learner_role):
    def make_learner(user, course):
        """Make `user` a learner in `course`."""
        assignment = factories.Assignment()
        factories.AssignmentGrouping(assignment=assignment, grouping=course)
        factories.AssignmentMembership(
            assignment=assignment, user=user, lti_role=learner_role
        )
        db_session.flush()

    return make_learner


@pytest.fixture(autouse=True)
def send(patch):
    return patch("lms.services.digest.send")
