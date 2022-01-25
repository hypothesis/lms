from unittest.mock import sentinel

import factory as factory_boy
import pytest
from sqlalchemy.exc import IntegrityError

from lms.models import CanvasGroup, Grouping, GroupingMembership
from lms.services.grouping import GroupingService, factory
from tests import factories

pytestmark = pytest.mark.usefixtures("course_service", "application_instance_service")


class TestGroupingService:
    CONTEXT_ID = "context_id"
    TOOL_CONSUMER_INSTANCE_GUID = "t_c_i_guid"

    @pytest.fixture
    def upsert_with_parent_args(self, svc):
        """A factory for generating random arguments for upsert_with_parent().

        Usage:

            svc.upsert_with_parent(**upsert_with_parent_args(...))

        """
        return factory_boy.make_factory(
            dict,
            tool_consumer_instance_guid=factories.TOOL_CONSUMER_INSTANCE_GUID,
            lms_id=factory_boy.Sequence(lambda n: f"lms_id_{n}"),
            lms_name=factory_boy.Sequence(lambda n: f"lms_name_{n}"),
            type_=factory_boy.Faker(
                "random_element",
                elements=[
                    Grouping.Type.CANVAS_SECTION,
                    Grouping.Type.CANVAS_GROUP,
                    Grouping.Type.BLACKBOARD_GROUP,
                ],
            ),
            parent=factory_boy.SubFactory(
                factories.Course,
                application_instance=svc.application_instance,
            ),
        )

    def test_upsert_with_parents_inserts(
        self, svc, db_session, upsert_with_parent_args
    ):
        test_grouping = svc.upsert_with_parent(**upsert_with_parent_args())

        assert db_session.query(CanvasGroup).one() == test_grouping

    def test_you_cant_upsert_a_grouping_whose_parent_has_a_different_application_instance(
        self, svc, application_instance_service, db_session, upsert_with_parent_args
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

        svc.upsert_with_parent(**upsert_with_parent_args(parent=parent))

        with pytest.raises(
            IntegrityError,
            match='insert or update on table "grouping" violates foreign key constraint "fk__grouping__parent_id__grouping"',
        ):
            db_session.flush()

    def test_upsert_with_parent_updates_existing_groupings(
        self, svc, db_session, upsert_with_parent_args
    ):
        # Insert an existing grouping into the DB.
        args = upsert_with_parent_args()
        svc.upsert_with_parent(**args)

        # Update the existing grouping.
        args["lms_name"] = new_name = "new_name"
        args["extra"] = new_extra = {"extra": "new"}
        updated_grouping = svc.upsert_with_parent(**args)

        # It should return a grouping with the updated values.
        assert updated_grouping.lms_name == new_name
        assert updated_grouping.extra == new_extra
        # The values should have been updated in the DB as well.
        db_grouping = db_session.query(Grouping).filter_by(id=updated_grouping.id).one()
        assert db_grouping.lms_name == new_name
        assert db_grouping.extra == new_extra

    def test_canvas_group_and_sections_dont_conflict(
        self, svc, db_session, upsert_with_parent_args
    ):
        group = svc.upsert_with_parent(
            **upsert_with_parent_args(
                lms_id="same_id", type_=Grouping.Type.CANVAS_GROUP
            )
        )
        section = svc.upsert_with_parent(
            **upsert_with_parent_args(
                lms_id="same_id", type_=Grouping.Type.CANVAS_SECTION
            )
        )

        assert group.authority_provided_id != section.authority_provided_id

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
