from unittest.mock import sentinel

import pytest

from lms.models import LMSGroupSet
from lms.services.group_set import GroupSetService, factory
from tests import factories


class TestGroupSetService:
    @pytest.mark.parametrize(
        "group_set,expected",
        [
            # No extra keys
            (
                {"id": "1", "name": "name", "extra": "value"},
                {"id": "1", "name": "name"},
            ),
            # String ID
            ({"id": 1111, "name": "name"}, {"id": "1111", "name": "name"}),
        ],
    )
    def test_set_group_sets(self, group_set, expected, svc, db_session):
        course = factories.Course(extra={}, lms_course=factories.LMSCourse())
        db_session.flush()

        svc.store_group_sets(course, [group_set])

        assert course.extra["group_sets"] == [expected]
        assert (
            db_session.query(LMSGroupSet)
            .filter_by(lms_course_id=course.lms_course.id, lms_id=str(group_set["id"]))
            .one()
            .name
            == group_set["name"]
        )

    @pytest.fixture
    def svc(self, db_session):
        return GroupSetService(db=db_session)


class TestFactory:
    def test_it(self, pyramid_request, GroupSetService, db_session):
        service = factory(sentinel.context, pyramid_request)

        GroupSetService.assert_called_once_with(db=db_session)
        assert service == GroupSetService.return_value

    @pytest.fixture
    def GroupSetService(self, patch):
        return patch("lms.services.group_set.GroupSetService")
