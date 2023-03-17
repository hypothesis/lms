from datetime import datetime
from unittest.mock import call, sentinel

import factory
import pytest
from h_matchers import Any

from lms.services.digest import (
    DigestContext,
    DigestService,
    UnifiedCourse,
    UnifiedUser,
    service_factory,
)
from lms.services.mailchimp import EmailRecipient, EmailSender
from tests import factories


class TestDigestService:
    def test_send_instructor_email_digests(
        self, svc, h_api, context, DigestContext, db_session, mailchimp_service, sender
    ):
        audience = ["userid1", "userid2"]
        context.unified_users = {
            "userid1": UnifiedUserFactory(h_userid="userid1"),
            "userid2": UnifiedUserFactory(h_userid="userid2"),
        }
        digests = context.instructor_digest.side_effect = [
            {"total_annotations": 1},
            {"total_annotations": 2},
        ]

        svc.send_instructor_email_digests(
            audience, sentinel.updated_after, sentinel.updated_before
        )

        h_api.get_annotations.assert_called_once_with(
            audience, sentinel.updated_after, sentinel.updated_before
        )
        DigestContext.assert_called_once_with(
            db_session, audience, tuple(h_api.get_annotations.return_value)
        )
        assert context.instructor_digest.call_args_list == [
            call(h_userid) for h_userid in audience
        ]
        assert mailchimp_service.send_template.call_args_list == [
            call(
                "instructor-email-digest",
                sender,
                recipient=EmailRecipient(unified_user.email, unified_user.display_name),
                template_vars=digest,
            )
            for unified_user, digest in zip(context.unified_users.values(), digests)
        ]

    def test_send_instructor_email_digests_doesnt_send_empty_digests(
        self, svc, context, mailchimp_service
    ):
        context.instructor_digest.return_value = {"total_annotations": 0}

        svc.send_instructor_email_digests(
            [sentinel.h_userid], sentinel.updated_after, sentinel.updated_before
        )

        mailchimp_service.send_template.assert_not_called()

    def test_send_instructor_email_digests_ignores_instructors_with_no_email_address(
        self, svc, context, mailchimp_service
    ):
        context.unified_users = {sentinel.h_userid: UnifiedUserFactory(email=None)}
        context.instructor_digest.return_value = {"total_annotations": 1}

        svc.send_instructor_email_digests(
            [sentinel.h_userid], sentinel.updated_after, sentinel.updated_before
        )

        mailchimp_service.send_template.assert_not_called()

    def test_send_instructor_email_digests_uses_override_to_email(
        self, svc, context, mailchimp_service
    ):
        context.instructor_digest.return_value = {"total_annotations": 1}

        svc.send_instructor_email_digests(
            [sentinel.h_userid],
            sentinel.updated_after,
            sentinel.updated_before,
            override_to_email=sentinel.override_to_email,
        )

        assert (
            mailchimp_service.send_template.call_args[1]["recipient"].email
            == sentinel.override_to_email
        )

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
        h_api.get_annotations.return_value = [
            sentinel.annotation1,
            sentinel.annotation2,
        ]
        return h_api

    @pytest.fixture
    def svc(self, db_session, h_api, mailchimp_service, sender):
        return DigestService(
            db=db_session,
            h_api=h_api,
            mailchimp_service=mailchimp_service,
            sender=sender,
        )


class TestDigestContext:
    def test_instructor_digest(self, db_session, make_instructor):
        courses = factories.Course.create_batch(2)
        instructor, learner = factories.User.create_batch(2)
        for course in courses:
            make_instructor(instructor, course)
        annotations = [
            *Annotation.create_batch(
                2,
                authority_provided_id=courses[0].authority_provided_id,
                userid=learner.h_userid,
            ),
            Annotation(
                authority_provided_id=courses[1].authority_provided_id,
                userid=learner.h_userid,
            ),
        ]
        context = DigestContext(db_session, [instructor.h_userid], annotations)

        digest = context.instructor_digest(instructor.h_userid)

        assert digest == {
            "total_annotations": 3,
            "courses": Any.list.containing(
                [
                    {"title": courses[0].lms_name, "num_annotations": 2},
                    {"title": courses[1].lms_name, "num_annotations": 1},
                ]
            ).only(),
        }

    def test_instructor_digest_removes_duplicate_courses(
        self, db_session, make_instructor
    ):
        course = factories.Course()
        sub_groupings = factories.CanvasSection.create_batch(2, parent=course)
        instructor, learner = factories.User.create_batch(2)
        make_instructor(instructor, course)
        annotations = [
            Annotation(
                authority_provided_id=sub_grouping.authority_provided_id,
                userid=learner.h_userid,
            )
            for sub_grouping in sub_groupings
        ]
        context = DigestContext(db_session, [instructor.h_userid], annotations)

        digest = context.instructor_digest(instructor.h_userid)

        assert digest == {
            "total_annotations": 2,
            "courses": [{"title": course.lms_name, "num_annotations": 2}],
        }

    def test_instructor_digest_removes_courses_with_no_learner_annotations(
        self, db_session, make_instructor
    ):
        course = factories.Course()
        instructor = factories.User()
        make_instructor(instructor, course)
        annotations = [
            Annotation(
                authority_provided_id=course.authority_provided_id,
                userid=instructor.h_userid,
            )
        ]
        context = DigestContext(db_session, [instructor.h_userid], annotations)

        digest = context.instructor_digest(instructor.h_userid)

        assert digest == {"total_annotations": 0, "courses": []}

    def test_instructor_digest_omits_courses_where_the_user_isnt_an_instructor(
        self, db_session, make_instructor
    ):
        course, other_course = factories.Course.create_batch(2)
        instructor, learner = factories.User.create_batch(2)
        make_instructor(instructor, other_course)
        annotations = [
            Annotation(
                authority_provided_id=course.authority_provided_id,
                userid=learner.h_userid,
            )
        ]
        context = DigestContext(db_session, [instructor.h_userid], annotations)

        digest = context.instructor_digest(instructor.h_userid)

        assert digest == {"total_annotations": 0, "courses": []}

    def test_unified_users(self, db_session):
        audience = factories.User.create_batch(2)
        annotations = Annotation.create_batch(2)
        annotators = [
            factories.User(h_userid=annotation["author"]["userid"])
            for annotation in annotations
        ]
        context = DigestContext(
            db_session, [user.h_userid for user in audience], annotations
        )

        unified_users = context.unified_users

        assert unified_users == {
            user.h_userid: UnifiedUser(
                h_userid=user.h_userid,
                user_ids=(user.id,),
                email=Any(),
                display_name=Any(),
            )
            for user in audience + annotators
        }
        assert context.unified_users is unified_users

    def test_unified_users_with_no_audience_or_annotations(self, db_session):
        context = DigestContext(db_session, [], [])

        assert context.unified_users == {}

    def test_unified_users_ignores_duplicate_userids(self, db_session):
        user = factories.User()
        context = DigestContext(
            db_session,
            [user.h_userid, user.h_userid],
            Annotation.create_batch(2, userid=user.h_userid),
        )

        unified_users = context.unified_users

        assert unified_users == {
            user.h_userid: UnifiedUser(
                h_userid=user.h_userid,
                user_ids=(user.id,),
                email=Any(),
                display_name=Any(),
            )
        }

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
    def test_unified_users_email(self, db_session, users, expected_email):
        db_session.add_all(users)

        context = DigestContext(db_session, ["id"], [])

        assert context.unified_users["id"].email == expected_email

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
    def test_unified_users_display_name(self, db_session, users, expected_display_name):
        db_session.add_all(users)

        context = DigestContext(db_session, ["id"], [])

        assert context.unified_users["id"].display_name == expected_display_name

    def test_unified_courses(self, db_session, make_instructor, make_learner):
        course = factories.Course()
        instructors = factories.User.create_batch(2)
        for instructor in instructors:
            make_instructor(instructor, course)
        learner = factories.User()
        make_learner(learner, course)
        section = factories.CanvasSection(parent=course)
        annotations = [
            Annotation(
                authority_provided_id=grouping.authority_provided_id,
                userid=learner.h_userid,
            )
            for grouping in (course, course, section, section)
        ]
        context = DigestContext(
            db_session, [instructor.h_userid for instructor in instructors], annotations
        )

        unified_courses = context.unified_courses

        assert unified_courses == {
            grouping.authority_provided_id: Any.instance_of(UnifiedCourse).with_attrs(
                {
                    "authority_provided_id": course.authority_provided_id,
                    "instructors": Any.tuple.containing(
                        [make_unified_user(instructor) for instructor in instructors]
                    ).only(),
                    "learner_annotations": Any.tuple.containing(annotations).only(),
                }
            )
            for grouping in (course, section)
        }
        assert context.unified_courses is unified_courses

    def test_unified_courses_with_multiple_groupings(self, db_session):
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
            Annotation(authority_provided_id=grouping.authority_provided_id)
            for grouping in courses + sub_groupings
        ]
        context = DigestContext(db_session, [], annotations)

        assert context.unified_courses == {
            authority_provided_id: Any.instance_of(UnifiedCourse).with_attrs(
                {"authority_provided_id": "course_id"}
            )
            for authority_provided_id in set(
                grouping.authority_provided_id for grouping in courses + sub_groupings
            )
        }

    def test_unified_courses_with_no_annotations(self, db_session):
        context = DigestContext(db_session, [], [])

        assert context.unified_courses == {}

    def test_unified_courses_title(self, db_session):
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
                Annotation(authority_provided_id=course.authority_provided_id)
                for course in courses
            ],
        )

        assert context.unified_courses["id"].title == "most_recent"

    def test_unified_courses_doesnt_count_learners(self, db_session, make_learner):
        course = factories.Course()
        learner = factories.User()
        make_learner(learner, course)
        annotation = Annotation(
            authority_provided_id=course.authority_provided_id, userid=learner.h_userid
        )
        context = DigestContext(db_session, [], [annotation])

        assert context.unified_courses == {
            course.authority_provided_id: Any.instance_of(UnifiedCourse).with_attrs(
                {"instructors": ()}
            )
        }

    def test_unified_courses_doesnt_count_instructor_annotations(
        self, db_session, make_instructor
    ):
        course = factories.Course()
        instructor = factories.User()
        make_instructor(instructor, course)
        annotation = Annotation(
            authority_provided_id=course.authority_provided_id,
            userid=instructor.h_userid,
        )
        context = DigestContext(db_session, [], [annotation])

        assert context.unified_courses == {
            course.authority_provided_id: Any.instance_of(UnifiedCourse).with_attrs(
                {"learner_annotations": ()}
            )
        }

    def test_unified_courses_doesnt_count_instructors_from_other_courses(
        self, db_session, make_instructor
    ):
        course, other_course = factories.Course.create_batch(2)
        user = factories.User()
        # `user` is an instructor in `other_course`.
        make_instructor(user, other_course)
        # `user` is a learner in `course` and has created an annotation.
        annotation = Annotation(
            authority_provided_id=course.authority_provided_id,
            userid=user.h_userid,
        )
        context = DigestContext(db_session, [], [annotation])

        assert context.unified_courses == {
            course.authority_provided_id: Any.instance_of(UnifiedCourse).with_attrs(
                {"instructors": (), "learner_annotations": (annotation,)}
            )
        }

    def test_unified_courses_doesnt_count_annotations_from_other_courses(
        self, db_session
    ):
        course, other_course = factories.Course.create_batch(2)
        course_annotation = Annotation(
            authority_provided_id=course.authority_provided_id
        )
        other_course_annotation = Annotation(
            authority_provided_id=other_course.authority_provided_id
        )
        context = DigestContext(
            db_session, [], [course_annotation, other_course_annotation]
        )

        assert context.unified_courses[course.authority_provided_id] == Any.instance_of(
            UnifiedCourse
        ).with_attrs({"learner_annotations": (course_annotation,)})

    def test_unified_courses_ignores_unknown_authority_provided_ids(self, db_session):
        context = DigestContext(
            db_session, [], [Annotation(authority_provided_id="unknown")]
        )

        assert context.unified_courses == {}


class TestServiceFactory:
    def test_it(self, pyramid_request, h_api, mailchimp_service, DigestService):
        settings = pyramid_request.registry.settings
        settings["mailchimp_digests_subaccount"] = sentinel.digests_subaccount
        settings["mailchimp_digests_email"] = sentinel.digests_from_email
        settings["mailchimp_digests_name"] = sentinel.digests_from_name

        service = service_factory(sentinel.context, pyramid_request)

        DigestService.assert_called_once_with(
            db=pyramid_request.db,
            h_api=h_api,
            mailchimp_service=mailchimp_service,
            sender=EmailSender(
                sentinel.digests_subaccount,
                sentinel.digests_from_email,
                sentinel.digests_from_name,
            ),
        )
        assert service == DigestService.return_value

    @pytest.fixture
    def DigestService(self, patch):
        return patch("lms.services.digest.DigestService")


class Annotation(factory.Factory):
    """
    A factory for annotation dicts.

    >>> Annotation()
    {'author': {'userid': 'acct:user_1@lms.hypothes.is'}, 'group': {'authority_provided_id': 'group_1'}}
    >>> Annotation(userid='acct:custom_username@lms.hypothes.is')
    {'author': {'userid': 'acct:custom_username@lms.hypothes.is'}, 'group': {'authority_provided_id': 'group_2'}}
    >>> Annotation(authority_provided_id='custom_id')
    {'author': {'userid': 'acct:user_2@lms.hypothes.is'}, 'group': {'authority_provided_id': 'custom_id'}}
    """

    class Meta:
        model = dict

    userid = factory.Sequence(lambda n: f"acct:user_{n}@lms.hypothes.is")
    authority_provided_id = factory.Sequence(lambda n: f"group_{n}")

    @factory.post_generation
    def post(obj, *_args, **_kwargs):  # pylint:disable=no-self-argument
        # pylint:disable=unsupported-assignment-operation,no-member
        obj["author"] = {"userid": obj.pop("userid")}
        obj["group"] = {"authority_provided_id": obj.pop("authority_provided_id")}
        return obj


class UnifiedUserFactory(factory.Factory):
    class Meta:
        model = UnifiedUser

    h_userid = factory.Sequence(lambda n: f"acct:user_{n}@lms.hypothes.is")
    user_ids = factory.LazyAttribute(
        lambda o: [
            user.id for user in factories.User.create_batch(2, h_userid=o.h_userid)
        ]
    )
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


def make_unified_user(user):
    return UnifiedUser(
        h_userid=user.h_userid,
        user_ids=(user.id,),
        email=user.email,
        display_name=user.display_name,
    )
