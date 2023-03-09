from unittest.mock import call, create_autospec, sentinel

import factory
import pytest
from h_matchers import Any

from lms.services.digest import (
    DigestHelper,
    DigestService,
    UnifiedCourse,
    UnifiedUser,
    UnknownAuthorityProvidedID,
    service_factory,
)
from lms.services.mailchimp import EmailRecipient, EmailSender
from tests import factories


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


class TestDigestService:
    def test_send_instructor_email_digests(
        self, svc, h_api, helper, UnifiedUser_, db_session, mailchimp_service, sender
    ):
        h_userids = [sentinel.userid1, sentinel.userid2]
        unified_users = UnifiedUser_.make.side_effect = [
            create_autospec(UnifiedUser, spec_set=True, instance=True),
            create_autospec(UnifiedUser, spec_set=True, instance=True),
        ]
        digests = helper.instructor_digest.side_effect = [
            {"total_annotations": 1},
            {"total_annotations": 2},
        ]

        svc.send_instructor_email_digests(
            h_userids, sentinel.updated_after, sentinel.updated_before
        )

        h_api.get_annotations.assert_called_once_with(
            h_userids, sentinel.updated_after, sentinel.updated_before
        )
        helper.unified_courses.assert_called_once_with(
            h_api.get_annotations.return_value
        )
        assert UnifiedUser_.make.call_args_list == [
            call(db_session, h_userid) for h_userid in h_userids
        ]
        assert helper.instructor_digest.call_args_list == [
            call(unified_user, helper.unified_courses.return_value)
            for unified_user in unified_users
        ]
        assert mailchimp_service.send_template.call_args_list == [
            call(
                "instructor-email-digest",
                sender,
                recipient=EmailRecipient(unified_user.email, unified_user.display_name),
                template_vars=digest,
            )
            for unified_user, digest in zip(unified_users, digests)
        ]

    def test_send_instructor_email_digests_doesnt_send_empty_digests(
        self, svc, helper, mailchimp_service
    ):
        helper.instructor_digest.return_value = {"total_annotations": 0}

        svc.send_instructor_email_digests(
            [sentinel.h_userid], sentinel.updated_after, sentinel.updated_before
        )

        mailchimp_service.send_template.assert_not_called()

    def test_send_instructor_email_digests_uses_override_to_email(
        self, svc, helper, mailchimp_service
    ):
        helper.instructor_digest.return_value = {"total_annotations": 1}

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

    @pytest.fixture
    def helper(self):
        return create_autospec(DigestHelper, instance=True, spec_set=True)

    @pytest.fixture
    def sender(self):
        return EmailSender(sentinel.subaccount, sentinel.from_email, sentinel.from_name)

    @pytest.fixture
    def svc(self, db_session, helper, h_api, mailchimp_service, sender):
        return DigestService(
            db=db_session,
            helper=helper,
            h_api=h_api,
            mailchimp_service=mailchimp_service,
            sender=sender,
        )

    @pytest.fixture(autouse=True)
    def UnifiedUser_(self, patch):
        return patch("lms.services.digest.UnifiedUser")


class TestUnifiedUser:
    def test_h_userid(self, unified_user):
        assert unified_user.h_userid == sentinel.h_userid

    def test_userids(self, unified_user, users):
        assert unified_user.user_ids == [user.id for user in users]

    def test_email(self, unified_user, users):
        users[0].email = None
        users[1].email = sentinel.email

        assert unified_user.email == sentinel.email

    def test_email_returns_None(self, unified_user, users):
        users[0].email = None
        users[1].email = None

        assert unified_user.email is None

    def test_display_name(self, unified_user, users):
        users[0].display_name = None
        users[1].display_name = sentinel.display_name

        assert unified_user.display_name == sentinel.display_name

    def test_display_name_returns_None(self, unified_user, users):
        users[0].display_name = None
        users[1].display_name = None

        assert unified_user.display_name is None

    def test_make(self, db_session):
        # Create two different users with the same h_userid but different
        # application instances.
        instances = factories.ApplicationInstance.create_batch(2)
        users = [
            factories.User(application_instance=instance, h_userid="id")
            for instance in instances
        ]

        unified_user = UnifiedUser.make(db_session, "id")

        assert unified_user.users == Any.list.containing(users).only()

    @pytest.fixture
    def users(self):
        return factories.User.build_batch(2, h_userid=sentinel.h_userid)

    @pytest.fixture
    def unified_user(self, users):
        return UnifiedUser(users)


class TestUnifiedCourse:
    def test_authority_provided_id(self, unified_course, courses):
        assert unified_course.authority_provided_id == courses[0].authority_provided_id

    def test_title(self, unified_course, courses):
        assert unified_course.title == courses[0].lms_name

    def test_learner_annotations(
        self, unified_course, db_session, courses, make_instructor
    ):
        learner, instructor = factories.User.create_batch(2)
        make_instructor(instructor, courses[1])
        learner_annotations = Annotation.create_batch(
            2,
            userid=learner.h_userid,
            authority_provided_id=courses[1].authority_provided_id,
        )
        instructor_annotations = Annotation.create_batch(
            2,
            userid=instructor.h_userid,
            authority_provided_id=courses[0].authority_provided_id,
        )
        unified_course.annotations.extend(learner_annotations)
        unified_course.annotations.extend(instructor_annotations)

        assert (
            unified_course.learner_annotations(db_session)
            == Any.list.containing(learner_annotations).only()
        )

    def test_is_instructor_returns_True(self, db_session, make_instructor):
        course = factories.Course()
        unified_course = UnifiedCourse([course])
        instructor = UnifiedUser([factories.User()])
        make_instructor(instructor.users[0], course)

        is_instructor = unified_course.is_instructor(db_session, instructor)

        assert is_instructor is True

    def test_is_instructor_returns_False(self, db_session):
        unified_course = UnifiedCourse([factories.Course()])

        is_instructor = unified_course.is_instructor(
            db_session, UnifiedUser([factories.User()])
        )

        assert is_instructor is False

    def test_get_courses(self, db_session):
        # Create two courses with different application instances but the same
        # authority_provided_id.
        instances = factories.ApplicationInstance.create_batch(2)
        courses = [
            factories.Course(application_instance=instance, authority_provided_id="id")
            for instance in instances
        ]

        assert (
            UnifiedCourse.get_courses(db_session, "id")
            == Any.list.containing(courses).only()
        )

    def test_make_with_a_course_grouping(self, db_session):
        course = factories.Course()

        unified_course = UnifiedCourse.make(db_session, course.authority_provided_id)

        assert unified_course.courses == [course]

    def test_make_with_a_sub_grouping(self, db_session):
        canvas_section = factories.CanvasSection()

        unified_course = UnifiedCourse.make(
            db_session, canvas_section.authority_provided_id
        )

        assert unified_course.courses == [canvas_section.parent]

    def test_make_with_an_unknown_authority_provided_id(self, db_session):
        with pytest.raises(UnknownAuthorityProvidedID):
            UnifiedCourse.make(db_session, "unknown_id")

    def test_make_with_multiple_courses(self, db_session):
        # If there are multiple course groupings with the same
        # authority_provided_id but different instances it finds them all.
        instances = factories.ApplicationInstance.create_batch(2)
        courses = [
            factories.Course(authority_provided_id="id", application_instance=instance)
            for instance in instances
        ]
        section = factories.CanvasSection(parent=courses[1])

        unified_course = UnifiedCourse.make(db_session, section.authority_provided_id)

        assert unified_course.courses == courses

    @pytest.fixture
    def courses(self):
        return factories.Course.create_batch(2, authority_provided_id="id")

    @pytest.fixture
    def unified_course(self, courses):
        return UnifiedCourse(courses)


class TestDigestHelper:
    def test_unified_courses_with_course_groups(self, helper):
        """It groups annotations by their courses."""
        courses = factories.Course.create_batch(2)
        course_0_annotations = Annotation.create_batch(
            2, authority_provided_id=courses[0].authority_provided_id
        )
        course_1_annotations = Annotation.create_batch(
            2, authority_provided_id=courses[1].authority_provided_id
        )

        unified_courses = helper.unified_courses(
            course_0_annotations + course_1_annotations
        )

        assert (
            unified_courses
            == Any.list.containing(
                [
                    UnifiedCourse(
                        courses=[courses[0]],
                        annotations=Any.list.containing(course_0_annotations).only(),
                    ),
                    UnifiedCourse(
                        courses=[courses[1]],
                        annotations=Any.list.containing(course_1_annotations).only(),
                    ),
                ]
            ).only()
        )

    def test_unified_courses_with_sub_groups(self, helper):
        """It groups annotations from sub-groups by their parent courses."""
        courses = factories.Course.create_batch(2)
        sections = factories.CanvasSection.create_batch(2, parent=courses[0])
        group = factories.BlackboardGroup(parent=courses[1])

        section_0_annotations = Annotation.create_batch(
            2, authority_provided_id=sections[0].authority_provided_id
        )
        section_1_annotations = Annotation.create_batch(
            2, authority_provided_id=sections[1].authority_provided_id
        )
        group_annotations = Annotation.create_batch(
            2, authority_provided_id=group.authority_provided_id
        )

        unified_courses = helper.unified_courses(
            section_0_annotations + section_1_annotations + group_annotations
        )

        assert (
            unified_courses
            == Any.list.containing(
                [
                    UnifiedCourse(
                        courses=[courses[0]],
                        annotations=Any.list.containing(
                            section_0_annotations + section_1_annotations
                        ).only(),
                    ),
                    UnifiedCourse(
                        courses=[courses[1]],
                        annotations=Any.list.containing(group_annotations).only(),
                    ),
                ]
            ).only()
        )

    def test_courses_with_sub_groups_crossing_instances(self, helper):
        """It handles sub-groups from different instances of the same course."""
        instances = factories.ApplicationInstance.create_batch(2)
        courses = [
            factories.Course(authority_provided_id="id", application_instance=instance)
            for instance in instances
        ]
        sections = [
            factories.CanvasSection(parent=courses[0]),
            factories.CanvasSection(parent=courses[1]),
        ]
        section_0_annotations = Annotation.create_batch(
            2, authority_provided_id=sections[0].authority_provided_id
        )
        section_1_annotations = Annotation.create_batch(
            2, authority_provided_id=sections[1].authority_provided_id
        )

        unified_courses = helper.unified_courses(
            section_0_annotations + section_1_annotations
        )

        assert unified_courses == [
            UnifiedCourse(
                courses=courses,
                annotations=Any.list.containing(
                    section_0_annotations + section_1_annotations
                ).only(),
            )
        ]

    def test_unified_courses_ignores_unknown_authority_provided_ids(self, helper):
        """It ignores annotations with unknown group authority_provided_id's."""
        annotations = Annotation.create_batch(2, authority_provided_id="unknown_id")

        unified_courses = helper.unified_courses(annotations)

        assert unified_courses == []

    def test_instructor_digest(self, helper, make_instructor):
        unified_courses = [
            UnifiedCourse([factories.Course()], [Annotation()]),
            UnifiedCourse([factories.Course()], Annotation.create_batch(2)),
        ]
        instructor = UnifiedUser([factories.User()])
        for unified_course in unified_courses:
            make_instructor(instructor.users[0], unified_course.courses[0])

        digest = helper.instructor_digest(instructor, unified_courses)

        assert digest == {
            "total_annotations": 3,
            "courses": Any.list.containing(
                [
                    {"title": unified_courses[0].title, "num_annotations": 1},
                    {"title": unified_courses[1].title, "num_annotations": 2},
                ]
            ).only(),
        }

    def test_instructor_digest_omits_courses_with_no_learner_annotations(
        self, helper, make_instructor
    ):
        instructor = UnifiedUser([factories.User()])
        unified_course = UnifiedCourse(
            [factories.Course()], [Annotation(userid=instructor.h_userid)]
        )
        make_instructor(instructor.users[0], unified_course.courses[0])

        digest = helper.instructor_digest(instructor, [unified_course])

        assert digest == {"total_annotations": 0, "courses": []}

    def test_instructor_digest_omits_courses_where_the_user_isnt_an_instructor(
        self, helper
    ):
        unified_course = UnifiedCourse([factories.Course()], [Annotation()])

        digest = helper.instructor_digest(
            UnifiedUser([factories.User()]), [unified_course]
        )

        assert digest == {"total_annotations": 0, "courses": []}

    @pytest.fixture
    def helper(self, db_session):
        return DigestHelper(db_session)


class TestServiceFactory:
    def test_it(
        self, pyramid_request, h_api, mailchimp_service, DigestHelper, DigestService
    ):
        settings = pyramid_request.registry.settings
        settings["mailchimp_digests_subaccount"] = sentinel.digests_subaccount
        settings["mailchimp_digests_email"] = sentinel.digests_from_email
        settings["mailchimp_digests_name"] = sentinel.digests_from_name

        service = service_factory(sentinel.context, pyramid_request)

        DigestHelper.assert_called_once_with(pyramid_request.db)
        DigestService.assert_called_once_with(
            db=pyramid_request.db,
            helper=DigestHelper.return_value,
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
    def DigestHelper(self, patch):
        return patch("lms.services.digest.DigestHelper")

    @pytest.fixture
    def DigestService(self, patch):
        return patch("lms.services.digest.DigestService")


@pytest.fixture
def instructor_role():
    return factories.LTIRole(value="Instructor")


@pytest.fixture
def make_instructor(db_session, instructor_role):
    def make_instructor(user, course):
        """Make `user` an instructor in `course`."""
        assignment = factories.Assignment()
        factories.AssignmentGrouping(assignment=assignment, grouping=course)
        factories.AssignmentMembership(
            assignment=assignment, user=user, lti_role=instructor_role
        )
        db_session.flush()

    return make_instructor
