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

    @pytest.mark.usefixtures("course_with_group_sets")
    @pytest.mark.parametrize(
        "params",
        (
            {"context_id": "context_id", "group_set_id": "ID", "name": "NAME"},
            {"context_id": "context_id", "name": "NAME"},
            {"context_id": "context_id", "name": "name"},
            {"context_id": "context_id", "name": "NAME    "},
            {"context_id": "context_id", "group_set_id": "ID"},
        ),
    )
    def test_find_group_set(self, svc, params, application_instance):
        group_set = svc.find_group_set(
            application_instance=application_instance, **params
        )

        assert group_set["id"] == "ID"
        assert group_set["name"] == "NAME"

    @pytest.mark.usefixtures("course_with_group_sets")
    @pytest.mark.parametrize(
        "params",
        (
            {"context_id": "context_id", "group_set_id": "NOID", "name": "NAME"},
            {"context_id": "context_id", "group_set_id": "ID", "name": "NONAME"},
            {"context_id": "no_context_id", "group_set_id": "ID", "name": "NAME"},
        ),
    )
    def test_find_group_set_no_matches(self, svc, params, application_instance):
        assert not svc.find_group_set(
            application_instance=application_instance, **params
        )

    @pytest.mark.usefixtures("course_with_group_sets")
    def test_find_group_set_returns_first_result(self, svc, application_instance):
        assert svc.find_group_set(application_instance)

    @pytest.fixture
    def svc(self, db_session):
        return GroupSetService(db=db_session)

    @pytest.fixture
    def course(self, application_instance):
        return factories.Course(
            application_instance=application_instance, lms_id="context_id"
        )

    @pytest.fixture
    def course_with_group_sets(self, course):
        course.extra = {
            "group_sets": [
                {
                    "id": "ID",
                    "name": "NAME",
                },
                {
                    "id": "NOT MATCHING ID NOISE",
                    "name": "NOT MATCHING NAME NOISE",
                },
            ]
        }
        return course


class TestFactory:
    def test_it(self, pyramid_request, GroupSetService, db_session):
        service = factory(sentinel.context, pyramid_request)

        GroupSetService.assert_called_once_with(db=db_session)
        assert service == GroupSetService.return_value

    @pytest.fixture
    def GroupSetService(self, patch):
        return patch("lms.services.group_set.GroupSetService")
