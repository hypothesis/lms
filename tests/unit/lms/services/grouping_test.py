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
        self, db_session, upsert_with_parent
    ):
        # Insert an existing grouping into the DB.
        upsert_with_parent(lms_name="old_name", extra={"extra": "old"})

        # upsert_with_parent() should find and update the existing grouping.
        new_name, new_extra = "new_name", {"extra": "new"}
        grouping = upsert_with_parent(lms_name=new_name, extra=new_extra)

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
        # GroupingService uses ApplicationInstanceService.get_current() as the
        # application_instance for the new grouping it inserts.
        # Here the parent course will have a different application_instance,
        # which will trigger an IntegrityError when we flush the DB.
        assert (
            parent.application_instance
            != application_instance_service.get_current.return_value
        )

        upsert_with_parent(parent=parent)

        with pytest.raises(
            IntegrityError,
            match='insert or update on table "grouping" violates foreign key constraint "fk__grouping__parent_id__grouping"',
        ):
            db_session.flush()

    def test_you_can_have_a_group_and_a_section_with_the_same_id(
        self, db_session, svc, upsert_with_parent
    ):
        course = factories.Course(application_instance=svc.application_instance)
        db_session.flush()

        canvas_group = upsert_with_parent(
            parent=course, type_=Grouping.Type.CANVAS_GROUP
        )
        canvas_section = upsert_with_parent(
            parent=course, type_=Grouping.Type.CANVAS_SECTION
        )
        blackboard_group = upsert_with_parent(
            parent=course, type_=Grouping.Type.BLACKBOARD_GROUP
        )

        # We've created three groupings witht the same application_instance, parent and lms_id.
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
    def upsert_with_parent(self, svc):
        return partial(
            svc.upsert_with_parent,
            tool_consumer_instance_guid="t_c_i_guid",
            lms_id="lms_id",
            lms_name="lms_name",
            parent=factories.Course(application_instance=svc.application_instance),
            type_=Grouping.Type.CANVAS_GROUP,
        )


class TestUpsertGroupingMemberships:
    @pytest.mark.parametrize("flushing", [True, False])
    def test_it(self, db_session, svc, flushing):
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
        if flushing:
            # upsert_grouping_memberships should flush itself if not done from the caller
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
    @pytest.mark.parametrize("group_set_id", [42, None])
    def test_it(
        self,
        db_session,
        svc,
        user,
        course,
        make_grouping,
        group_set_id,
    ):
        # A grouping that is in the right course, that the user is a member of,
        # that is the right type, and that has the right group_set_id.
        # get_course_groupings_for_user() should always return this grouping.
        matching_grouping = make_grouping()

        # A grouping that belongs to the wrong group set.
        # get_course_groupings_for_user() should return this grouping if no
        # group_set_id argument is given but not if a group_set_id=42 argument
        # is given.
        grouping_with_wrong_group_set_id = make_grouping(group_set_id=56)

        # A grouping that the user isn't a member of.
        # get_course_groupings_for_user() should not return this.
        make_grouping(membership=False)

        # A grouping that is in the wrong course.
        # get_course_groupings_for_user() should not return this.
        make_grouping(parent=factories.Course())

        # A grouping that has the wrong type.
        # get_course_groupings_for_user() should not return this.
        make_grouping(factory=factories.CanvasGroup)

        # Flush the session to generate IDs.
        db_session.flush()

        groupings = svc.get_course_groupings_for_user(
            course,
            user.user_id,
            Grouping.Type.CANVAS_SECTION,
            group_set_id=group_set_id,
        )

        expected_groupings = [matching_grouping]
        if not group_set_id:
            # If we didn't pass a group_set_id argument to
            # get_course_groupings_for_user() then it will return groupings
            # with any group_set_id.
            expected_groupings.append(grouping_with_wrong_group_set_id)
        assert groupings == Any.iterable.containing(expected_groupings).only()

    @pytest.fixture
    def course(self):
        """Return the course that we'll ask for groupings from."""
        return factories.Course()

    @pytest.fixture
    def user(self):
        """Return the user whose groupings we'll ask for."""
        return factories.User()

    @pytest.fixture
    def make_grouping(self, db_session, course, user):
        """Return a factory for making groupings."""

        def make_grouping(
            factory=factories.CanvasSection,
            parent=None,
            group_set_id=42,
            membership=True,
        ):
            parent = parent or course

            grouping = factory(parent=parent, extra={"group_set_id": group_set_id})

            if membership:
                db_session.add(GroupingMembership(user=user, grouping=grouping))
            else:
                # Add a *different* user as a member of the group, otherwise DB
                # queries wouldn't return the grouping even if the code didn't
                # filter by user_id.
                db_session.add(
                    GroupingMembership(user=factories.User(), grouping=grouping)
                )

            return grouping

        return make_grouping


class TestFactory:
    def test_it(self, pyramid_request):
        grouping_service = factory(sentinel.context, pyramid_request)

        assert isinstance(grouping_service, GroupingService)


@pytest.fixture
def svc(db_session, application_instance_service):
    return GroupingService(db_session, application_instance_service)
