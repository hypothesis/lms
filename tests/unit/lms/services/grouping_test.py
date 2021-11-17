from unittest.mock import sentinel

import pytest

from lms.models import Grouping
from lms.models._hashed_id import hashed_id
from lms.services.grouping import GroupingService, factory
from tests import factories

pytestmark = pytest.mark.usefixtures("course_service", "application_instance_service")


class TestGroupingService:
    CONTEXT_ID = "context_id"
    TOOL_CONSUMER_INSTANCE_GUID = "t_c_i_guid"

    def test_upsert_with_parents_inserts(self, svc, db_session):
        application_instance = factories.ApplicationInstance()

        # Start with no groupings
        assert not db_session.query(Grouping).count()

        test_grouping = svc.upsert_with_parent(
            tool_consumer_instance_guid=application_instance.tool_consumer_instance_guid,
            lms_id="lms_id",
            lms_name="lms_name",
            parent=None,
            type_=Grouping.Type.COURSE,
        )

        assert db_session.query(Grouping).one() == test_grouping

    def test_upsert_with_parents_updates(self, svc, db_session, application_instance):
        grouping = factories.Grouping(application_instance=application_instance)
        db_session.flush()

        grouping.lms_name = "new_name"
        grouping.extra = {"extra": "extra"}

        grouping = svc.upsert_with_parent(
            tool_consumer_instance_guid=grouping.application_instance.tool_consumer_instance_guid,
            lms_id=grouping.lms_id,
            lms_name=grouping.lms_name,
            parent=None,
            type_=grouping.type,
            extra=grouping.extra,
        )

        db_grouping = db_session.query(Grouping).one()
        assert db_grouping.lms_name == "new_name"
        assert db_grouping.extra == {"extra": "extra"}

    def test_canvas_group_and_sections_dont_conflict(self, svc, db_session):
        course = factories.Course()
        db_session.flush()

        group = svc.upsert_with_parent(
            self.TOOL_CONSUMER_INSTANCE_GUID,
            "group_id",
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

        assert group.type == Grouping.Type.CANVAS_GROUP
        assert section.type == Grouping.Type.CANVAS_SECTION
        assert group.authority_provided_id != section.authority_provided_id
        assert group.parent_id == section.parent_id == course.id

    def test_generate_authority_provided_id_section(self, svc, db_session):
        course = factories.Course()
        db_session.flush()

        assert (
            svc.generate_authority_provided_id(
                self.TOOL_CONSUMER_INSTANCE_GUID,
                "section_id",
                course,
                Grouping.Type.CANVAS_SECTION,
            )
            == hashed_id(self.TOOL_CONSUMER_INSTANCE_GUID, course.lms_id, "section_id")
        )

    def test_generate_authority_provided_id_course(self, svc):
        assert (
            svc.generate_authority_provided_id(
                self.TOOL_CONSUMER_INSTANCE_GUID,
                "course_id",
                parent=None,
                type_=Grouping.Type.COURSE,
            )
            == hashed_id(self.TOOL_CONSUMER_INSTANCE_GUID, "course_id")
        )

    def test_generate_authority_provided_id(self, svc, db_session):
        course = factories.Course()
        db_session.flush()

        assert svc.generate_authority_provided_id(
            self.TOOL_CONSUMER_INSTANCE_GUID,
            "group_id",
            course,
            Grouping.Type.CANVAS_GROUP,
        ) == hashed_id(
            self.TOOL_CONSUMER_INSTANCE_GUID,
            course.lms_id,
            Grouping.Type.CANVAS_GROUP,
            "group_id",
        )

    @pytest.fixture
    def svc(self, db_session, application_instance_service):
        return GroupingService(db_session, application_instance_service)


class TestFactory:
    def test_it(self, pyramid_request):
        grouping_service = factory(sentinel.context, pyramid_request)

        assert isinstance(grouping_service, GroupingService)
