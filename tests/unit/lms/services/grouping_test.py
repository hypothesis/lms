from unittest.mock import sentinel

import pytest

from lms.models import CanvasGroup, Grouping, GroupingMembership
from lms.services.grouping import GroupingService, factory
from tests import factories

pytestmark = pytest.mark.usefixtures("course_service", "application_instance_service")


class TestGroupingService:
    CONTEXT_ID = "context_id"
    TOOL_CONSUMER_INSTANCE_GUID = "t_c_i_guid"

    def test_upsert_with_parents_inserts(self, svc, db_session):
        course = factories.Course()

        # Start with no CanvasGroup
        assert not db_session.query(CanvasGroup).count()

        test_grouping = svc.upsert_with_parent(
            tool_consumer_instance_guid=course.application_instance.tool_consumer_instance_guid,
            lms_id="lms_id",
            lms_name="lms_name",
            parent=course,
            type_=Grouping.Type.CANVAS_GROUP,
        )

        assert db_session.query(CanvasGroup).one() == test_grouping

    def test_upsert_with_parent_updates_existing_groupings(self, svc, db_session):
        course = factories.Course()
        kwargs = {
            "tool_consumer_instance_guid": course.application_instance.tool_consumer_instance_guid,
            "lms_id": "lms_id",
            "parent": course,
            "type_": Grouping.Type.CANVAS_GROUP,
        }
        old_name = "old_name"
        old_extra = {"extra": "old"}
        new_name = "new_name"
        new_extra = {"extra": "new"}
        # Insert an existing grouping into the DB.
        svc.upsert_with_parent(lms_name=old_name, extra=old_extra, **kwargs)

        # upsert_with_parent() should find and update the existing grouping.
        grouping = svc.upsert_with_parent(lms_name=new_name, extra=new_extra, **kwargs)

        # It should return a grouping with the updated values.
        assert grouping.lms_name == new_name
        assert grouping.extra == new_extra
        # The values should have been updated in the DB as well.
        db_grouping = db_session.query(CanvasGroup).one()
        assert db_grouping.lms_name == new_name
        assert db_grouping.extra == new_extra

    def test_canvas_group_and_sections_dont_conflict(self, svc, db_session):
        course = factories.Course(lms_id=self.CONTEXT_ID)
        db_session.flush()

        group = svc.upsert_with_parent(
            self.TOOL_CONSUMER_INSTANCE_GUID,
            "same_id",
            "group_name",
            course,
            Grouping.Type.CANVAS_GROUP,
        )
        section = svc.upsert_with_parent(
            self.TOOL_CONSUMER_INSTANCE_GUID,
            "same_id",
            "section_name",
            course,
            Grouping.Type.CANVAS_SECTION,
        )

        assert group.authority_provided_id == "078cc1b793e061085ed3ef91189b41a6f7dd26b8"
        assert (
            section.authority_provided_id == "867c2696d32eb4b5e9cf5c5304cb71c3e20bfd14"
        )
        assert group.type == Grouping.Type.CANVAS_GROUP
        assert section.type == Grouping.Type.CANVAS_SECTION
        assert group.parent_id == section.parent_id == course.id

    def test_generate_authority_provided_id_for_course(self, svc):
        assert (
            svc.generate_authority_provided_id(
                self.TOOL_CONSUMER_INSTANCE_GUID, "lms_id", None, Grouping.Type.COURSE
            )
            == "f56fc198fea84f419080e428f0ee2a7c0e2c132a"
        )

    @pytest.mark.parametrize(
        "type_,expected",
        [
            (Grouping.Type.CANVAS_SECTION, "0d671acc7759d5a5d06c724bb4bf7bf26419b9ba"),
            (Grouping.Type.CANVAS_GROUP, "aaab80699a478e9da17e734f2e3c8126687e6135"),
        ],
    )
    def test_generate_authority_provided_id_with_parent(
        self, svc, db_session, type_, expected
    ):
        course = factories.Course(lms_id="course_id")
        db_session.flush()

        assert (
            svc.generate_authority_provided_id(
                self.TOOL_CONSUMER_INSTANCE_GUID, "lms_id", course, type_
            )
            == expected
        )

    def test_upsert_grouping_memberships_inserts(
        self, svc, application_instance, db_session
    ):
        courses = factories.Course.create_batch(5)
        user = factories.User(application_instance=application_instance)
        assert not db_session.query(GroupingMembership).count()

        svc.upsert_grouping_memberships(user, courses)

        assert db_session.query(GroupingMembership).count() == len(courses)
        for course in courses:
            assert course.memberships[0].user == user

    def test_upsert_grouping_memberships_updates(
        self, svc, db_session, with_course_memberships
    ):
        user, courses = with_course_memberships

        svc.upsert_grouping_memberships(user, courses)

        assert db_session.query(GroupingMembership).filter_by(user=user).count() == len(
            courses
        )

    def test_get_course_grouping_for_user(self, svc, with_group_memberships):
        user, courses, group_a = with_group_memberships

        groupings = svc.get_course_groupings_for_user(
            courses[0], user.user_id, Grouping.Type.CANVAS_GROUP
        )

        assert len(groupings) == 1
        assert groupings[0] == group_a

    def test_get_course_grouping_for_user_with_groupset_id(
        self, svc, with_group_memberships
    ):
        user, courses, group_a = with_group_memberships

        groupings = svc.get_course_groupings_for_user(
            courses[0],
            user.user_id,
            Grouping.Type.CANVAS_GROUP,
            group_a.extra["group_set_id"],
        )

        assert len(groupings) == 1
        assert groupings[0] == group_a

    def test_get_course_grouping_for_user_with_different_groupset_id(
        self, svc, with_group_memberships
    ):
        user, courses, _ = with_group_memberships

        groupings = svc.get_course_groupings_for_user(
            courses[0], user.user_id, Grouping.Type.CANVAS_GROUP, "ANOTHER_GROUP_SET_ID"
        )

        assert not groupings

    def test_get_course_grouping_for_user_with_different_type(
        self, svc, with_group_memberships
    ):
        user, courses, _ = with_group_memberships

        groupings = svc.get_course_groupings_for_user(
            courses[0], user.user_id, Grouping.Type.CANVAS_SECTION
        )

        assert not groupings

    def test_get_course_grouping_for_user_with_different_course(
        self, svc, with_group_memberships
    ):
        user, courses, _ = with_group_memberships

        groupings = svc.get_course_groupings_for_user(
            courses[1], user.user_id, Grouping.Type.CANVAS_GROUP
        )

        assert not groupings

    def test_get_course_grouping_for_user_with_different_user(
        self, svc, with_group_memberships, application_instance
    ):
        _, courses, _ = with_group_memberships
        other_user = factories.User(application_instance=application_instance)

        groupings = svc.get_course_groupings_for_user(
            courses[0], other_user.user_id, Grouping.Type.CANVAS_GROUP
        )

        assert not groupings

    @pytest.fixture
    def with_course_memberships(self, svc, application_instance):
        courses = factories.Course.create_batch(5)
        user = factories.User(application_instance=application_instance)

        svc.upsert_grouping_memberships(user, courses)

        # Some extra courses/user for noise
        factories.Course.create_batch(5)
        factories.User(application_instance=application_instance)

        return user, courses

    @pytest.fixture
    def with_group_memberships(self, with_course_memberships, db_session):
        user, courses = with_course_memberships

        course = courses[0]
        group_a = CanvasGroup(
            parent=course,
            authority_provided_id="section_a",
            application_instance=course.application_instance,
            lms_id="SECTION_A",
            lms_name="SECTION_A",
            extra={"group_set_id": "GROUPSET_ID"},
        )
        # An extra group for noise
        group_b = CanvasGroup(
            authority_provided_id="section_b",
            parent=course,
            application_instance=course.application_instance,
            lms_id="SECTION_B",
            lms_name="SECTION_B",
        )

        db_session.add_all(
            [group_a, group_b, GroupingMembership(user=user, grouping=group_a)]
        )

        return user, courses, group_a

    @pytest.fixture
    def svc(self, db_session, application_instance_service):
        return GroupingService(db_session, application_instance_service)


class TestFactory:
    def test_it(self, pyramid_request):
        grouping_service = factory(sentinel.context, pyramid_request)

        assert isinstance(grouping_service, GroupingService)
