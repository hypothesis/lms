from functools import partial
from unittest.mock import sentinel

import pytest
from h_matchers import Any
from sqlalchemy.exc import IntegrityError

from lms.models import CanvasGroup, Grouping, GroupingMembership
from lms.services.grouping import GroupingService, factory
from tests import factories

pytestmark = pytest.mark.usefixtures("application_instance_service")


class TestGenerateAuthorityProvidedID:
    def test_generating_an_authority_provided_id_for_a_course(
        self, generate_authority_provided_id
    ):
        assert (
            generate_authority_provided_id(parent=None, type_=Grouping.Type.COURSE)
            == "f56fc198fea84f419080e428f0ee2a7c0e2c132a"
        )

    def test_it_raises_if_a_course_grouping_has_a_parent(
        self, generate_authority_provided_id
    ):
        with pytest.raises(
            AssertionError, match="Course groupings can't have a parent"
        ):
            generate_authority_provided_id(
                parent=factories.Course(), type_=Grouping.Type.COURSE
            )

    @pytest.mark.parametrize(
        "type_",
        [
            Grouping.Type.CANVAS_SECTION,
            Grouping.Type.CANVAS_GROUP,
            Grouping.Type.BLACKBOARD_GROUP,
        ],
    )
    def test_it_raises_if_a_child_grouping_has_no_parent(
        self, generate_authority_provided_id, type_
    ):
        with pytest.raises(
            AssertionError, match="Non-course groupings must have a parent"
        ):
            generate_authority_provided_id(parent=None, type_=type_)

    @pytest.mark.parametrize(
        "type_,expected",
        [
            (Grouping.Type.CANVAS_SECTION, "0d671acc7759d5a5d06c724bb4bf7bf26419b9ba"),
            (Grouping.Type.CANVAS_GROUP, "aaab80699a478e9da17e734f2e3c8126687e6135"),
            (
                Grouping.Type.BLACKBOARD_GROUP,
                "4ce0683ddacadfd58168afaf7cb7301024f46531",
            ),
        ],
    )
    def test_generating_an_authority_provided_id_for_a_child_grouping(
        self, generate_authority_provided_id, type_, expected
    ):
        assert (
            generate_authority_provided_id(
                parent=factories.Course(lms_id="course_id"), type_=type_
            )
            == expected
        )

    @pytest.fixture
    def generate_authority_provided_id(self):
        return partial(
            GroupingService.generate_authority_provided_id, "t_c_i_guid", "lms_id"
        )


class TestUpsertWithParent:
    def test_if_no_grouping_already_exists_it_inserts_a_new_one(
        self, db_session, upsert_with_parent
    ):
        test_grouping = upsert_with_parent()

        assert db_session.query(CanvasGroup).one() == test_grouping

    def test_if_a_grouping_already_exists_it_updates_it(
        self, db_session, svc, upsert_with_parent
    ):

        parent = factories.Course(application_instance=svc.application_instance)
        # Insert an existing grouping into the DB.
        upsert_with_parent(
            parent=parent,
            lms_name="old_name",
            extra={"extra": "old"},
        )

        # upsert_with_parent() should find and update the existing grouping.
        new_name, new_extra = "new_name", {"extra": "new"}
        grouping = upsert_with_parent(parent=parent, lms_name=new_name, extra=new_extra)

        # It should return a grouping with the updated values.
        assert grouping.lms_name == new_name
        assert grouping.extra == new_extra
        # The values should have been updated in the DB as well.
        db_grouping = db_session.query(CanvasGroup).one()
        assert db_grouping.lms_name == new_name
        assert db_grouping.extra == new_extra

    def test_you_cant_upsert_a_grouping_whose_parent_has_a_different_application_instance(
        self, application_instance_service, db_session, upsert_with_parent
    ):
        parent = factories.Course()
        db_session.flush()
        # GroupingService uses ApplicationInstanceService.get_current() as the
        # application_instance for the new grouping it inserts.
        # Here the parent course will have a different application_instance,
        # which will trigger an IntegrityError when we flush the DB.
        assert (
            parent.application_instance
            != application_instance_service.get_current.return_value
        )

        with pytest.raises(
            IntegrityError,
            match='insert or update on table "grouping" violates foreign key constraint "fk__grouping__parent_id__grouping"',
        ):
            upsert_with_parent(parent=parent)

    def test_you_can_have_a_group_and_a_section_with_the_same_id(
        self, db_session, svc, upsert_with_parent
    ):
        course = factories.Course(application_instance=svc.application_instance)
        db_session.flush()

        canvas_group = upsert_with_parent(
            parent=course, type=Grouping.Type.CANVAS_GROUP
        )
        canvas_section = upsert_with_parent(
            parent=course, type=Grouping.Type.CANVAS_SECTION
        )
        blackboard_group = upsert_with_parent(
            parent=course, type=Grouping.Type.BLACKBOARD_GROUP
        )

        # We've created three groupings with the same application_instance, parent and lms_id.
        assert (
            canvas_group.application_instance
            == canvas_section.application_instance
            == blackboard_group.application_instance
        )
        assert (
            canvas_group.parent_id
            == canvas_section.parent_id
            == blackboard_group.parent_id
        )
        assert canvas_group.lms_id == canvas_section.lms_id == blackboard_group.lms_id
        # But they have a different type and therefore a different authority_provided_id.
        assert canvas_group.type != canvas_section.type
        assert canvas_group.type != blackboard_group.type
        assert blackboard_group.type != canvas_section.type
        assert (
            canvas_group.authority_provided_id != canvas_section.authority_provided_id
        )
        assert (
            canvas_group.authority_provided_id != blackboard_group.authority_provided_id
        )
        assert (
            blackboard_group.authority_provided_id
            != canvas_section.authority_provided_id
        )

    @pytest.fixture
    def upsert_with_parent(self, svc, db_session):
        def upsert_with_parent_single_item(**kwargs):
            params = dict(
                lms_id="lms_id",
                lms_name="lms_name",
                parent=factories.Course(application_instance=svc.application_instance),
                type=Grouping.Type.CANVAS_GROUP,
            )
            params.update(**kwargs)

            db_session.flush()
            return svc.upsert_with_parent([params])[0]

        return upsert_with_parent_single_item


class TestUpsertGroupingMemberships:
    def test_it(self, db_session, svc):
        user = factories.User()
        groups = []
        # Create a group that the user is already a member of.
        group_that_user_was_already_a_member_of = factories.Course()
        groups.append(group_that_user_was_already_a_member_of)
        db_session.add(
            GroupingMembership(
                grouping=group_that_user_was_already_a_member_of,
                user=user,
            )
        )
        # Add a group that the user is not yet a member of.
        groups.append(factories.CanvasGroup())
        db_session.flush()

        svc.upsert_grouping_memberships(user, groups)

        # The user should now be a member of both groups.
        assert (
            db_session.query(GroupingMembership)
            == Any.iterable.containing(
                [
                    Any.object.of_type(GroupingMembership).with_attrs(
                        {
                            "grouping_id": group.id,
                            "user_id": user.id,
                        }
                    )
                    for group in groups
                ]
            ).only()
        )


class TestGetCourseGroupingsForUser:
    def test_it_with_no_group_set_id(self, svc, with_group_memberships):
        """
        Test it with no group_set_id argument.

        If not group_set_id argument is given it returns all the child
        groupings that the user belongs to.
        """
        user, courses, group_a = with_group_memberships

        groupings = svc.get_course_groupings_for_user(
            courses[0], user.user_id, Grouping.Type.CANVAS_GROUP
        )

        assert len(groupings) == 1
        assert groupings[0] == group_a

    def test_it_with_a_group_set_id(self, svc, with_group_memberships):
        """
        Test it with a group_set_id.

        If a group_set_id argument is given it returns only the groupings with
        that group_set_id.
        """
        user, courses, group_a = with_group_memberships

        groupings = svc.get_course_groupings_for_user(
            courses[0],
            user.user_id,
            Grouping.Type.CANVAS_GROUP,
            group_a.extra["group_set_id"],
        )

        assert len(groupings) == 1
        assert groupings[0] == group_a

    def test_it_doesnt_return_groupings_that_have_a_different_group_set_id(
        self, svc, with_group_memberships
    ):
        user, courses, _ = with_group_memberships

        groupings = svc.get_course_groupings_for_user(
            courses[0], user.user_id, Grouping.Type.CANVAS_GROUP, "ANOTHER_GROUP_SET_ID"
        )

        assert not groupings

    def test_it_doesnt_return_groupings_that_have_a_different_type(
        self, svc, with_group_memberships
    ):
        user, courses, _ = with_group_memberships

        groupings = svc.get_course_groupings_for_user(
            courses[0], user.user_id, Grouping.Type.CANVAS_SECTION
        )

        assert not groupings

    def test_it_doesnt_return_groupings_that_belong_to_a_different_course(
        self, svc, with_group_memberships
    ):
        user, courses, _ = with_group_memberships

        groupings = svc.get_course_groupings_for_user(
            courses[1], user.user_id, Grouping.Type.CANVAS_GROUP
        )

        assert not groupings

    def test_it_doesnt_return_groupings_that_the_user_isnt_a_member_of(
        self, svc, with_group_memberships, application_instance
    ):
        _, courses, _ = with_group_memberships
        other_user = factories.User(application_instance=application_instance)

        groupings = svc.get_course_groupings_for_user(
            courses[0], other_user.user_id, Grouping.Type.CANVAS_GROUP
        )

        assert not groupings

    @pytest.fixture
    def with_course_memberships(self, svc, db_session, application_instance):
        courses = factories.Course.create_batch(5)
        user = factories.User(application_instance=application_instance)
        db_session.flush()

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


class TestFactory:
    def test_it(self, pyramid_request):
        grouping_service = factory(sentinel.context, pyramid_request)

        assert isinstance(grouping_service, GroupingService)


@pytest.fixture
def svc(db_session, application_instance_service):
    return GroupingService(db_session, application_instance_service)
