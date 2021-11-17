from unittest.mock import sentinel

import pytest

from lms.models import CanvasGroup, Grouping
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

    def test_upsert_with_parents_updates(self, svc, db_session):
        course = factories.Course()
        tool_consumer_instance_guid = (
            course.application_instance.tool_consumer_instance_guid
        )
        lms_id = "lms_id"
        old_name = "old_name"
        old_extra = {"extra": "old"}
        new_name = "new_name"
        new_extra = {"extra": "new"}

        # Insert a new grouping.
        svc.upsert_with_parent(
            tool_consumer_instance_guid=tool_consumer_instance_guid,
            lms_id=lms_id,
            lms_name=old_name,
            parent=course,
            type_=Grouping.Type.CANVAS_GROUP,
            extra=old_extra,
        )

        # Update the previously-inserted grouping with new values.
        grouping = svc.upsert_with_parent(
            tool_consumer_instance_guid=tool_consumer_instance_guid,
            lms_id=lms_id,
            lms_name=new_name,
            parent=course,
            type_=Grouping.Type.CANVAS_GROUP,
            extra=new_extra,
        )

        # upsert_with_parent() should return a Grouping that has the updated values.
        assert grouping.lms_name == new_name
        assert grouping.extra == new_extra

        # The Grouping's values should have been updated in the DB as well.
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

    @pytest.fixture
    def svc(self, db_session, application_instance_service):
        return GroupingService(db_session, application_instance_service)


class TestFactory:
    def test_it(self, pyramid_request):
        grouping_service = factory(sentinel.context, pyramid_request)

        assert isinstance(grouping_service, GroupingService)
