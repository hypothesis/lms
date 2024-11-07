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
    def test_set_group_sets(self, group_set, expected, svc, db_session, course):
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

    @pytest.mark.usefixtures("group_sets")
    @pytest.mark.parametrize(
        "params",
        (
            {"context_id": "context_id", "lms_id": "ID", "name": "NAME"},
            {"context_id": "context_id", "name": "NAME"},
            {"context_id": "context_id", "name": "name"},
            {"context_id": "context_id", "name": "NAME    "},
            {"context_id": "context_id", "lms_id": "ID"},
        ),
    )
    def test_find_group_set(self, svc, params, application_instance):
        group_set = svc.find_group_set(
            application_instance=application_instance, **params
        )

        assert group_set.lms_id == "ID"
        assert group_set.name == "NAME"

    @pytest.mark.usefixtures("group_sets")
    @pytest.mark.parametrize(
        "params",
        (
            {"context_id": "context_id", "lms_id": "NOID", "name": "NAME"},
            {"context_id": "context_id", "lms_id": "ID", "name": "NONAME"},
            {"context_id": "no_context_id", "lms_id": "ID", "name": "NAME"},
        ),
    )
    def test_find_group_set_no_matches(self, svc, params, application_instance):
        assert not svc.find_group_set(
            application_instance=application_instance, **params
        )

    @pytest.mark.usefixtures("group_sets")
    def test_find_group_set_returns_first_result(self, svc, application_instance):
        assert svc.find_group_set(application_instance)

    @pytest.fixture
    def svc(self, db_session):
        return GroupSetService(db=db_session)

    @pytest.fixture
    def course(self, application_instance):
        course = factories.Course(
            application_instance=application_instance,
            lms_id="context_id",
            lms_course=factories.LMSCourse(lti_context_id="context_id"),
        )
        factories.LMSCourseApplicationInstance(
            lms_course=course.lms_course, application_instance=application_instance
        )
        return course

    @pytest.fixture
    def group_sets(self, course, db_session):
        factories.LMSGroupSet(name="NAME", lms_id="ID", lms_course=course.lms_course)
        factories.LMSGroupSet(
            name="NOT MATCHING", lms_id="NOT MATCHING", lms_course=course.lms_course
        )
        db_session.flush()


class TestFactory:
    def test_it(self, pyramid_request, GroupSetService, db_session):
        service = factory(sentinel.context, pyramid_request)

        GroupSetService.assert_called_once_with(db=db_session)
        assert service == GroupSetService.return_value

    @pytest.fixture
    def GroupSetService(self, patch):
        return patch("lms.services.group_set.GroupSetService")
