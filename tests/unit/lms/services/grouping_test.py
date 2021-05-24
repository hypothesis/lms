import pytest
from unittest.mock import sentinel


from lms.services.grouping import GroupingService, factory
from tests import factories

pytestmark = pytest.mark.usefixtures("course_service")


class TestGroupingService:
    def test_course_grouping_updates_name(self, svc, course_service):
        course_service.get_or_create.return_value = factories.Course()

        course = svc.course_grouping("guid", "new name", "context_id")

        assert course.name == "new name"

    @pytest.fixture
    def svc(self, db_session, course_service):
        return GroupingService(db_session, course_service)


class TestFactory:
    def test_it(self, pyramid_request):
        grouping_service = factory(sentinel.context, pyramid_request)

        assert isinstance(grouping_service, GroupingService)
