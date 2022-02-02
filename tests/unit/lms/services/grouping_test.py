from functools import partial
from unittest.mock import sentinel

import pytest
from h_matchers import Any

from lms.models import Grouping, GroupingMembership
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
    def test_it(self, db_session, svc):
        # Create a parent course for the groupings to belong to.
        # The course has to belong to svc.application_instance.
        course = factories.Course(application_instance=svc.application_instance)
        # A pre-existing grouping that we'll update.
        existing_grouping = {
            "lms_id": "existing_id",
            "lms_name": "existing_name",
            "extra": {"existing": "extra"},
        }
        # Unfortunately we have to use upsert_with_parent() itself to insert the pre-existing grouping.
        svc.upsert_with_parent(
            [existing_grouping],
            type_=Grouping.Type.CANVAS_GROUP,
            parent=course,
        )

        # Upsert one grouping that already exists and one that doesn't exist yet.
        groupings = svc.upsert_with_parent(
            [
                # The pre-existing grouping to update.
                {
                    "lms_id": existing_grouping["lms_id"],
                    # We'll update existing_grouping's lms_name and extra.
                    "lms_name": "updated_name",
                    "extra": {"updated": "extra"},
                },
                # The new grouping to create.
                {
                    "lms_id": "new_grouping_id",
                    "lms_name": "new_grouping_name",
                    "extra": {"new": "extra"},
                },
            ],
            type_=Grouping.Type.CANVAS_GROUP,
            parent=course,
        )

        # It should have updated the existing grouping.
        existing_grouping = (
            db_session.query(Grouping).filter_by(lms_id="existing_id").one()
        )
        assert existing_grouping.lms_name == "updated_name"
        assert existing_grouping.extra == {"updated": "extra"}

        # It should have created the new grouping.
        new_grouping = (
            db_session.query(Grouping).filter_by(lms_id="new_grouping_id").one()
        )
        assert new_grouping.lms_name == "new_grouping_name"
        assert new_grouping.parent == course
        assert new_grouping.extra == {"new": "extra"}

        assert existing_grouping in groupings
        assert new_grouping in groupings

    def test_you_can_have_a_group_and_a_section_with_the_same_id(self, svc):
        course = factories.Course(application_instance=svc.application_instance)

        common_grouping_args = {"lms_id": "same_lms_id", "lms_name": "same_name"}

        canvas_group = svc.upsert_with_parent(
            [common_grouping_args], parent=course, type_=Grouping.Type.CANVAS_GROUP
        )[0]
        canvas_section = svc.upsert_with_parent(
            [common_grouping_args], parent=course, type_=Grouping.Type.CANVAS_SECTION
        )[0]
        blackboard_group = svc.upsert_with_parent(
            [common_grouping_args], parent=course, type_=Grouping.Type.BLACKBOARD_GROUP
        )[0]

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
