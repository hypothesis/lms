from unittest.mock import sentinel

import pytest
from sqlalchemy.orm import make_transient

from lms.models import Grouping
from lms.models._hashed_id import hashed_id
from lms.services.grouping import GroupingService, factory
from tests import factories

pytestmark = pytest.mark.usefixtures("course_service", "application_instance_service")


class TestGroupingService:
    CONTEXT_ID = "context_id"
    TOOL_CONSUMER_INSTANCE_GUID = "t_c_i_guid"

    def test_upsert_inserts(self, svc, db_session):
        # Start with no groupings
        assert not db_session.query(Grouping).count()

        test_grouping = Grouping(
            application_instance=factories.ApplicationInstance(),
            authority_provided_id="ID",
            lms_id="lms_id",
            lms_name="lms_name",
        )

        svc.upsert(test_grouping)

        assert db_session.query(Grouping).one() == test_grouping

    def test_upsert_updates(self, svc, db_session):
        grouping = factories.Grouping()
        db_session.flush()

        # Treat `grouping` as it was a freshly created object
        make_transient(grouping)

        grouping.lms_name = "new_name"
        grouping.extra = {"extra": "extra"}

        grouping = svc.upsert(grouping)

        db_grouping = db_session.query(Grouping).one()
        assert db_grouping.lms_name == "new_name"
        assert db_grouping.extra == {"extra": "extra"}

    def test_canvas_section_finds_course(self, svc, course_service, db_session):
        course_service.get.return_value = factories.Course()
        db_session.flush()

        grouping = svc.upsert_canvas_section(
            self.TOOL_CONSUMER_INSTANCE_GUID,
            self.CONTEXT_ID,
            "section_id",
            "section_name",
        )

        course_service.generate_authority_provided_id.assert_called_once_with(
            self.TOOL_CONSUMER_INSTANCE_GUID, self.CONTEXT_ID
        )
        course_service.get.assert_called_once_with(
            course_service.generate_authority_provided_id.return_value
        )
        assert grouping.parent_id == course_service.get.return_value.id

    def test_canvas_group_finds_course(self, svc, course_service, db_session):
        course_service.get.return_value = factories.Course()
        db_session.flush()

        grouping = svc.upsert_canvas_group(
            self.TOOL_CONSUMER_INSTANCE_GUID,
            self.CONTEXT_ID,
            "group_id",
            "group_name",
            "group_set_id",
        )

        course_service.get.assert_called_once_with(
            hashed_id(self.TOOL_CONSUMER_INSTANCE_GUID, self.CONTEXT_ID),
        )
        assert grouping.parent_id == course_service.get.return_value.id

    def test_canvas_group_and_sections_dont_conflict(
        self, svc, course_service, db_session
    ):
        course_service.get.return_value = factories.Course(lms_id=self.CONTEXT_ID)
        db_session.flush()

        group = svc.upsert_canvas_group(
            self.TOOL_CONSUMER_INSTANCE_GUID,
            self.CONTEXT_ID,
            "same_id",
            "group_name",
            "group_set_id",
        )
        section = svc.upsert_canvas_section(
            self.TOOL_CONSUMER_INSTANCE_GUID,
            self.CONTEXT_ID,
            "same_id",
            "section_name",
        )

        assert group.authority_provided_id == "078cc1b793e061085ed3ef91189b41a6f7dd26b8"
        assert (
            section.authority_provided_id == "867c2696d32eb4b5e9cf5c5304cb71c3e20bfd14"
        )
        assert (
            group.parent_id == section.parent_id == course_service.get.return_value.id
        )

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

        print(course.lms_id)
        assert (
            svc.generate_authority_provided_id(
                self.TOOL_CONSUMER_INSTANCE_GUID, "lms_id", course, type_
            )
            == expected
        )

    @pytest.fixture
    def svc(self, db_session, course_service, application_instance_service):
        return GroupingService(db_session, application_instance_service, course_service)


class TestFactory:
    def test_it(self, pyramid_request):
        grouping_service = factory(sentinel.context, pyramid_request)

        assert isinstance(grouping_service, GroupingService)
