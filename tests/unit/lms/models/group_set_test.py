from unittest.mock import sentinel

import pytest

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
    def test_set_group_sets(self, group_set, expected, svc):
        course = factories.Course(extra={})

        svc.store_group_sets(course, [group_set])

        assert course.extra["group_sets"] == [expected]

    def test_get_group_sets(self, svc):
        course = factories.Course(extra={"group_sets": sentinel.group_sets})

        assert svc.get_group_sets(course) == sentinel.group_sets

    def test_get_group_set_empty(self, svc):
        course = factories.Course(extra={})

        assert not svc.get_group_sets(course)

    @pytest.fixture
    def svc(self):
        return GroupSetService()


class TestFactory:
    def test_it(self, pyramid_request, GroupSetService):
        service = factory(sentinel.context, pyramid_request)

        GroupSetService.assert_called_once_with()
        assert service == GroupSetService.return_value

    @pytest.fixture
    def GroupSetService(self, patch):
        return patch("lms.services.group_set.GroupSetService")
