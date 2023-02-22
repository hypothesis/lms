from datetime import datetime
from unittest.mock import sentinel

import pytest

from lms.models import Grouping
from lms.services.digest import (
    CourseDigest,
    CourseGroupings,
    DigestService,
    InstructorDigest,
    UserRecords,
    factory,
)
from lms.services.h_api import Annotation, Group, User
from tests import factories


class TestUserRecords:
    def test_email_returns_the_email_from_the_first_user_that_has_one(self):
        user_1 = factories.User(h_userid=sentinel.h_userid, email=None)
        user_2 = factories.User(h_userid=sentinel.h_userid, email="user@example.com")
        user_records = UserRecords(sentinel.h_userid, [user_1, user_2])

        assert user_records.email == user_2.email

    def test_email_returns_None_if_none_of_the_users_have_an_email(self):
        user_1 = factories.User(h_userid=sentinel.h_userid, email=None)
        user_2 = factories.User(h_userid=sentinel.h_userid, email=None)
        user_records = UserRecords(sentinel.h_userid, [user_1, user_2])

        assert not user_records.email

    def test_name_returns_the_display_name_from_the_first_user_that_has_one(self):
        user_1 = factories.User(h_userid=sentinel.h_userid, display_name=None)
        user_2 = factories.User(
            h_userid=sentinel.h_userid, display_name=sentinel.display_name
        )
        user_records = UserRecords(sentinel.h_userid, [user_1, user_2])

        assert user_records.name == user_2.display_name

    def test_name_returns_None_if_none_of_the_users_have_a_display_name(self):
        user_1 = factories.User(h_userid=sentinel.h_userid, display_name=None)
        user_2 = factories.User(h_userid=sentinel.h_userid, display_name=None)
        user_records = UserRecords(sentinel.h_userid, [user_1, user_2])

        assert not user_records.name


class TestCourseGroupings:
    def test_title(self):
        courses = factories.Course.build_batch(
            2, authority_provided_id=sentinel.authority_provided_id
        )
        course_groupings = CourseGroupings(courses)

        assert course_groupings.title == courses[0].lms_name


class TestGetInstructorDigest:
    def test_it_calls_the_h_API(self, svc, instructors, since, until, h_api):
        svc.get_instructor_digest(h_userids(instructors), since, until)

        h_api.get_annotations.assert_called_once_with(
            h_userids(instructors), since, until
        )

    def test_it_when_there_are_no_annotations(
        self, svc, instructors, since, until, h_api
    ):
        h_api.get_annotations.return_value = iter([])

        digests = svc.get_instructor_digest(
            [instructor.h_userid for instructor in instructors], since, until
        )

        assert digests == {
            instructor.h_userid: InstructorDigest(instructor, {})
            for instructor in instructors
        }

    def test_it_counts_annotations_in_course_groups(
        self, create_annotation, make_instructors, svc, instructors, since, until
    ):
        # Make each user in `instructors` an instructor in one course.
        courses = factories.Course.create_batch(size=len(instructors))
        for course, instructor in zip(courses, instructors):
            make_instructors(course, [instructor])

        # Create one annotation in each course.
        annotator = factories.User.build()
        annotations = [create_annotation(annotator, course) for course in courses]

        digests = svc.get_instructor_digest(h_userids(instructors), since, until)

        # Each instructor's digest should include only the course(s) that
        # they're an instructor in and the annotation(s) in each course.
        assert digests == {
            instructor.h_userid: InstructorDigest(
                instructor,
                courses={
                    course.authority_provided_id: CourseDigest(
                        course=CourseGroupings([course]),
                        users={annotation.user: [annotation]},
                    )
                },
            )
            for instructor, course, annotation in zip(instructors, courses, annotations)
        }

    def test_it_counts_annotations_in_non_course_groups(
        self, create_annotation, make_instructors, svc, instructors, since, until, h_api
    ):
        # Make a Canvas Section grouping in which each user in `instructors` is
        # an instructor, and make an annotation in that section.
        section = factories.CanvasSection()
        make_instructors(section, instructors)
        annotation = create_annotation(factories.User(), section)
        h_api.get_annotations.return_value = [annotation]

        digests = svc.get_instructor_digest(h_userids(instructors), since, until)

        # In their digests the instructors should see the Canvas section's
        # parent course and the annotation that was created in the section.
        assert digests == {
            user.h_userid: InstructorDigest(
                user,
                courses={
                    section.parent.authority_provided_id: CourseDigest(
                        course=CourseGroupings([section.parent]),
                        users={annotation.user: [annotation]},
                    )
                },
            )
            for user in instructors
        }

    def test_it_sums_annotations_in_sub_groups_belonging_to_the_same_course(
        self, create_annotation, make_instructors, svc, instructors, since, until
    ):
        # Create a course grouping with two sub-groupings and an annotation in
        # each sub-grouping.
        course = factories.Course()
        make_instructors(course, instructors)
        sections = factories.CanvasSection.create_batch(2, parent=course)
        annotator = factories.User()
        annotations = [create_annotation(annotator, section) for section in sections]

        digests = svc.get_instructor_digest(h_userids(instructors), since, until)

        assert digests == {
            instructor.h_userid: InstructorDigest(
                instructor,
                courses={
                    course.authority_provided_id: CourseDigest(
                        course=CourseGroupings([course]),
                        users={User(username=annotator.h_userid): annotations},
                    )
                },
            )
            for instructor in instructors
        }

    def test_it_sums_annotations_across_application_instances(
        self, create_annotation, make_instructors, instructors, svc, since, until
    ):
        # Create two groupings for the same course but with different application instances.
        instructor = instructors[0]
        application_instances = factories.ApplicationInstance.create_batch(2)
        authority_provided_id = "authority_provided_id"
        courses = [
            factories.Course(
                application_instance=application_instance,
                authority_provided_id=authority_provided_id,
            )
            for application_instance in application_instances
        ]
        # The instructor only needs to be an instructor in one instance of the course.
        make_instructors(courses[0], [instructor])
        # We only need one annotation.
        annotator = factories.User()
        annotation = create_annotation(annotator, courses[0])

        digests = svc.get_instructor_digest([instructor.h_userid], since, until)

        assert digests == {
            instructor.h_userid: InstructorDigest(
                instructor,
                courses={
                    authority_provided_id: CourseDigest(
                        course=CourseGroupings(courses),
                        users={User(username=annotator.h_userid): [annotation]},
                    )
                },
            )
        }

    def test_it_doesnt_count_annotations_from_instructors(
        self, create_annotation, make_instructors, svc, instructors, since, until, h_api
    ):
        course = factories.Course()
        make_instructors(course, instructors)

        # An instructor who is not one of our audience users.
        other_instructor = factories.User()
        other_instructor = UserRecords(other_instructor.h_userid, [other_instructor])
        make_instructors(course, [other_instructor])

        h_api.get_annotations.return_value = [
            create_annotation(other_instructor, course)
        ]

        digests = svc.get_instructor_digest(h_userids(instructors), since, until)

        assert digests == {
            user.h_userid: InstructorDigest(user, courses={}) for user in instructors
        }

    def test_it_doesnt_count_annotations_from_unknown_groups(
        self, create_annotation, svc, instructors, since, until
    ):
        create_annotation(factories.User.build(), factories.CanvasGroup.build())

        digests = svc.get_instructor_digest(h_userids(instructors), since, until)

        assert digests == {
            user.h_userid: InstructorDigest(user, courses={}) for user in instructors
        }

    @pytest.fixture
    def instructor_role(self):
        return factories.LTIRole(value="Instructor")

    @pytest.fixture
    def since(self):
        return datetime(year=2023, month=2, day=20)

    @pytest.fixture
    def until(self):
        return datetime(year=2023, month=2, day=21)

    @pytest.fixture
    def instructors(self, db_session):
        instructors = factories.User.create_batch(size=2)
        db_session.flush()  # Flush the DB to generate user IDs.
        return [
            UserRecords(h_userid=instructor.h_userid, user_records=[instructor])
            for instructor in instructors
        ]

    @pytest.fixture
    def svc(self, db_session, h_api):
        return DigestService(db_session, h_api)

    @pytest.fixture
    def make_instructors(self, instructor_role):
        def make_instructors(grouping, user_records):
            """Make the given users instructors in the given grouping's course."""
            assignment = create_assignment(grouping)
            for user_record in user_records:
                factories.AssignmentMembership(
                    assignment=assignment,
                    user=user_record.user_records[0],
                    lti_role=instructor_role,
                )

        return make_instructors

    @pytest.fixture
    def create_annotation(self, h_api):
        def create_annotation(annotator, grouping):
            """Create an annotation by the given user in the given grouping."""
            annotation = Annotation(
                user=User(username=annotator.h_userid),
                group=Group(authority_provided_id=grouping.authority_provided_id),
            )
            h_api.get_annotations.return_value.append(annotation)
            return annotation

        return create_annotation


class TestFactory:
    def test_it(self, pyramid_request, DigestService, h_api):
        svc = factory(sentinel.context, pyramid_request)

        DigestService.assert_called_once_with(pyramid_request.db, h_api)
        assert svc == DigestService.return_value

    @pytest.fixture
    def DigestService(self, patch):
        return patch("lms.services.digest.DigestService")


def create_assignment(grouping):
    """Create an assignment in the given grouping or its parent course."""
    assignment = factories.Assignment()

    if grouping.type == Grouping.Type.COURSE:
        course = grouping
    else:
        course = grouping.parent

    factories.AssignmentGrouping(assignment=assignment, grouping=course)

    return assignment


def h_userids(users):
    return [user.h_userid for user in users]
