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

    def test_upsert_inserts(self, svc):
        # Start with no groupings
        assert not svc._db.query(Grouping).count()

        grouping = svc.upsert(
            Grouping(
                application_instance=factories.ApplicationInstance(),
                authority_provided_id="ID",
                lms_id="lms_id",
                lms_name="lms_name",
            )
        )
        assert svc._db.query(Grouping).count() == 1

    def test_upsert_updates(self, svc):
        grouping = factories.Grouping()
        svc._db.flush()

        grouping.lms_name = "new_name"

        grouping = svc.upsert(grouping)

        db_grouping = svc._db.query(Grouping).one()
        assert db_grouping.lms_name == "new_name"

    def test_section_grouping_finds_course(
        self, svc, course_service, application_instance_service
    ):
        application_instance_service.get.return_value = factories.ApplicationInstance()
        course_service.get_or_create.return_value = factories.Course()

        grouping = svc.section_grouping(
            self.TOOL_CONSUMER_INSTANCE_GUID,
            self.CONTEXT_ID,
            "section_id",
            "section_name",
        )

        course_service.get_or_create.assert_called_once_with(
            hashed_id(self.TOOL_CONSUMER_INSTANCE_GUID, self.CONTEXT_ID),
            self.CONTEXT_ID,
            None,
            None,
        )
        assert grouping.parent == course_service.get_or_create.return_value

    def test_course_grouping_updates_name(self, svc, course_service):
        course_service.get_or_create.return_value = factories.Course()

        course = svc.course_grouping("guid", "new name", "context_id")

        assert course.name == "new name"

    @pytest.fixture
    def svc(self, db_session, course_service, application_instance_service):
        return GroupingService(db_session, application_instance_service, course_service)


class TestFactory:
    def test_it(self, pyramid_request):
        grouping_service = factory(sentinel.context, pyramid_request)

        assert isinstance(grouping_service, GroupingService)
