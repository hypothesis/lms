from unittest.mock import create_autospec

import pytest
from h_matchers import Any

from lms.models import CanvasGroup, Course, Grouping, GroupingMembership
from lms.services.grouping import GroupingService, factory
from lms.services.grouping._plugin import GroupingServicePlugin
from tests import factories


class TestGetAuthorityProvidedID:
    def test_it_for_courses(self, svc):
        assert (
            svc.get_authority_provided_id(lms_id="lms_id", type_=Grouping.Type.COURSE)
            == "f56fc198fea84f419080e428f0ee2a7c0e2c132a"
        )

    def test_it_raises_if_a_course_grouping_has_a_parent(self, svc):
        with pytest.raises(
            AssertionError, match="Course groupings can't have a parent"
        ):
            svc.get_authority_provided_id(
                lms_id="any", parent=factories.Course(), type_=Grouping.Type.COURSE
            )

    @pytest.mark.parametrize(
        "type_",
        [
            Grouping.Type.CANVAS_SECTION,
            Grouping.Type.CANVAS_GROUP,
            Grouping.Type.BLACKBOARD_GROUP,
        ],
    )
    def test_it_raises_if_a_child_grouping_has_no_parent(self, svc, type_):
        with pytest.raises(
            AssertionError, match="Non-course groupings must have a parent"
        ):
            svc.get_authority_provided_id(lms_id="any", parent=None, type_=type_)

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
    def test_it_for_a_child_grouping(self, svc, type_, expected):
        assert (
            svc.get_authority_provided_id(
                lms_id="lms_id",
                parent=factories.Course(lms_id="course_id"),
                type_=type_,
            )
            == expected
        )

    @pytest.fixture
    def application_instance(self, application_instance):
        application_instance.tool_consumer_instance_guid = "t_c_i_guid"
        return application_instance


class TestUpsertGroupings:
    def test_it_with_empty_list(self, svc, parent_course):
        assert not svc.upsert_groupings(
            [],
            type_=Grouping.Type.CANVAS_GROUP,
            parent=parent_course,
        )

    @pytest.mark.parametrize("pre_flush", (True, False))
    def test_it_can_create_new(self, db_session, svc, parent_course, pre_flush):
        if pre_flush:
            db_session.flush()
        else:
            assert parent_course.id is None
        attrs = {
            "lms_id": "new_id",
            # We'll update existing_grouping's lms_name and extra.
            "lms_name": "new_name",
            "extra": {"created": "extra"},
        }
        if pre_flush:
            db_session.flush()
        else:
            assert parent_course.id is None

        groupings = svc.upsert_groupings(
            [attrs],
            type_=Grouping.Type.CANVAS_GROUP,
            parent=parent_course,
        )

        created_grouping = db_session.query(CanvasGroup).one()
        assert groupings == [created_grouping]
        assert created_grouping == Any.object.with_attrs(attrs)
        assert created_grouping == Any.object.with_attrs(
            {
                "application_instance": svc.application_instance,
                "authority_provided_id": Any.string(),
                "updated": Any(),
                "parent": parent_course,
                "type": Grouping.Type.CANVAS_GROUP,
            }
        )

    def test_it_updates_existing(
        self, db_session, svc, parent_course, existing_grouping
    ):
        attrs = {
            "lms_id": existing_grouping.lms_id,
            # We'll update existing_grouping's lms_name and extra.
            "lms_name": "new_name",
            "extra": {"updated": "extra"},
        }

        groupings = svc.upsert_groupings(
            [attrs],
            type_=Grouping.Type.CANVAS_GROUP,
            parent=parent_course,
        )

        # Load the changes we made in SQLAlchemy
        db_session.refresh(existing_grouping)

        assert groupings == [existing_grouping]
        assert existing_grouping == Any.object.with_attrs(attrs)

    def test_it_with_new_course(self, svc):
        attrs = {
            "lms_id": "course_id",
            "lms_name": "course_name",
            "extra": {"created": "extra"},
            "settings": {"created": "settings"},
        }

        courses = svc.upsert_groupings([attrs], type_=Grouping.Type.COURSE)

        assert courses == [Any.instance_of(Course).with_attrs(attrs)]

    def test_it_updates_courses(self, db_session, svc, parent_course):
        # We need to flush the new course out, otherwise we get weird conflicts
        db_session.flush()

        attrs = {
            "lms_id": parent_course.lms_id,
            "lms_name": "new_name",
            "extra": {"updated": "extra"},
        }

        courses = svc.upsert_groupings(
            [dict(attrs, settings={"IGNORED": True})], type_=Grouping.Type.COURSE
        )

        # Load the changes we made in SQLAlchemy
        db_session.refresh(parent_course)
        assert courses == [parent_course]
        assert parent_course == Any.object.with_attrs(attrs)

    @pytest.fixture
    def parent_course(self, svc):
        lms_id = "course_id"

        return factories.Course.create(
            lms_id=lms_id,
            application_instance=svc.application_instance,
            authority_provided_id=svc.get_authority_provided_id(
                lms_id, Grouping.Type.COURSE
            ),
        )

    @pytest.fixture
    def existing_grouping(self, parent_course, svc):
        lms_id = "existing_id"

        return factories.CanvasGroup.create(
            lms_id=lms_id,
            lms_name="existing_name",
            extra={"existing": "extra"},
            parent=parent_course,
            # Construct the authority_provided_id correctly, otherwise we get
            # a fake one generated by factory boy that doesn't line up
            authority_provided_id=svc.get_authority_provided_id(
                lms_id, Grouping.Type.CANVAS_GROUP, parent_course
            ),
            application_instance=parent_course.application_instance,
        )


class TestUpsertGroupingMemberships:
    @pytest.mark.parametrize("flushing", [True, False])
    def test_it(self, db_session, svc, flushing, user):
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


@pytest.fixture
def plugin():
    return create_autospec(GroupingServicePlugin, spec_set=True, instance=True)


@pytest.fixture
def svc(db_session, application_instance, plugin):
    return GroupingService(db_session, application_instance, plugin=plugin)
