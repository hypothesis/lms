import datetime
from unittest.mock import sentinel

import pytest

from lms.models import Course, CourseGroupsExportedFromH, Grouping
from lms.services.course import CourseService, course_service_factory
from tests import factories


class TestCourseService:
    @pytest.mark.parametrize(
        "settings_set,value,expected",
        (
            ([], "any", False),
            ([{"group": {"key": "match"}}], "match", True),
            ([{"group": {"key": "no_match"}}], "match", False),
            (
                [{"group": {"key": "no_match"}}, {"group": {"key": "match"}}],
                "match",
                True,
            ),
        ),
    )
    def test_any_with_setting(
        self, svc, settings_set, value, expected, application_instance
    ):
        for settings in settings_set:
            factories.Course(
                application_instance=application_instance, settings=settings
            )

        # Add a matching course with a different consumer key
        factories.Course(
            application_instance=factories.ApplicationInstance(),
            settings={"group": {"key": value}},
        )

        assert svc.any_with_setting("group", "key", value) is expected

    def test_get_by_context_id(self, svc, course):
        assert svc.get_by_context_id(course.lms_id) == course

    def test_get_by_context_id_with_no_match(self, svc):
        assert svc.get_by_context_id("NO MATCH") is None

    def test_upsert_returns_existing(self, svc, db_session, course):
        new_course = svc.upsert(
            context_id=course.lms_id, name="new course name", extra={}
        )

        # No new courses created
        assert db_session.query(Course).count() == 1
        # And existing course has been updated
        assert new_course.lms_name == "new course name"

    def test_upsert_creates_new(self, svc, db_session, grouping_service):
        # Starting with a fresh DB
        assert not db_session.query(Course).count()

        course = svc.upsert("context_id", "new course name", {})

        grouping_service.get_authority_provided_id.assert_called_once_with(
            lms_id="context_id", type_=Grouping.Type.COURSE
        )
        assert db_session.query(Course).count() == 1
        assert (
            course.authority_provided_id
            == grouping_service.get_authority_provided_id.return_value
        )
        assert course.lms_id == "context_id"

    @pytest.mark.parametrize("canvas_sections_enabled", [True, False])
    def test_upsert_sets_canvas_sections_enabled_based_on_legacy_rows(
        self,
        application_instance,
        db_session,
        svc,
        canvas_sections_enabled,
        grouping_service,
    ):
        db_session.add(
            CourseGroupsExportedFromH(
                authority_provided_id=grouping_service.get_authority_provided_id.return_value,
                created=datetime.datetime.utcnow(),
            )
        )
        application_instance.settings.set(
            "canvas", "sections_enabled", canvas_sections_enabled
        )

        svc.upsert("context_id", "new course name", {})

        course = db_session.query(Course).one()
        assert not course.settings.get("canvas", "sections_enabled")

    @pytest.fixture
    def course(self, application_instance, grouping_service):
        return factories.Course(
            application_instance=application_instance,
            authority_provided_id=grouping_service.get_authority_provided_id.return_value,
            lms_id="context_id",
        )

    @pytest.fixture
    def application_instance(self, application_instance):
        application_instance.tool_consumer_instance_guid = "tool_consumer_instance_guid"
        return application_instance

    @pytest.fixture
    def grouping_service(self, grouping_service):
        grouping_service.get_authority_provided_id.return_value = (
            "AUTHORITY_PROVIDED_ID"
        )

        return grouping_service

    @pytest.fixture
    def svc(self, db_session, application_instance, grouping_service):
        return CourseService(
            db=db_session,
            application_instance=application_instance,
            grouping_service=grouping_service,
        )


class TestCourseServiceFactory:
    def test_it(
        self,
        pyramid_request,
        application_instance_service,
        grouping_service,
        CourseService,
    ):
        svc = course_service_factory(sentinel.context, pyramid_request)

        application_instance_service.get_current.assert_called_once_with()

        CourseService.assert_called_once_with(
            db=pyramid_request.db,
            application_instance=application_instance_service.get_current.return_value,
            grouping_service=grouping_service,
        )

        assert svc == CourseService.return_value

    @pytest.fixture
    def CourseService(self, patch):
        return patch("lms.services.course.CourseService")
