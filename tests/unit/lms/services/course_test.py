import datetime
from unittest.mock import sentinel

import pytest

from lms.models import Course, CourseGroupsExportedFromH, Grouping
from lms.services.course import CourseService, course_service_factory
from tests import factories


class TestCourseService:
    @pytest.mark.parametrize("canvas_sections_enabled", [True, False])
    def test_it_inserts_False_if_theres_a_matching_row_in_course_groups_exported_from_h(
        self,
        application_instance,
        db_session,
        svc,
        canvas_sections_enabled,
        generate_authority_provided_id,
    ):
        db_session.add(
            CourseGroupsExportedFromH(
                authority_provided_id=generate_authority_provided_id.return_value,
                created=datetime.datetime.utcnow(),
            )
        )
        application_instance.settings.set(
            "canvas", "sections_enabled", canvas_sections_enabled
        )

        svc.upsert("context_id", "new course name", {})

        course = db_session.query(Course).one()
        assert not course.settings.get("canvas", "sections_enabled")

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
        self, svc, settings_set, value, expected, add_courses_with_settings
    ):
        add_courses_with_settings(settings_set)
        # Add a matching course with a different consumer key
        add_courses_with_settings(
            [{"group": {"key": value}}],
            application_instance=factories.ApplicationInstance(),
        )

        assert svc.any_with_setting("group", "key", value) is expected

    @pytest.mark.usefixtures("with_course")
    def test_upsert_returns_existing(self, svc, application_instance, db_session):
        course = svc.upsert("context_id", "new course name", {})
        # No new courses created
        assert db_session.query(Course).count() == 1

        # And existing course has been updated
        assert course.lms_name == "new course name"

    def test_upsert_creates_new(
        self, svc, db_session, application_instance, generate_authority_provided_id
    ):
        # Starting with a fresh DB
        assert not db_session.query(Course).count()

        course = svc.upsert("context_id", "new course name", {})

        assert db_session.query(Course).count() == 1

        generate_authority_provided_id.assert_called_once_with(
            tool_consumer_instance_guid=application_instance.tool_consumer_instance_guid,
            lms_id="context_id",
            parent=None,
            type_=Grouping.Type.COURSE,
        )
        assert (
            course.authority_provided_id == generate_authority_provided_id.return_value
        )
        assert course.lms_id == "context_id"

    @pytest.mark.usefixtures("with_course")
    def test_get_by_context_id(self, svc, application_instance):
        course = svc.get_by_context_id("context_id")

        assert course.lms_id == "context_id"
        assert (
            course.application_instance.tool_consumer_instance_guid
            == application_instance.tool_consumer_instance_guid
        )

    @pytest.fixture
    def add_courses_with_settings(self, application_instance):
        def add_courses_with_settings(
            settings_set, application_instance=application_instance
        ):
            for settings in settings_set:
                factories.Course(
                    application_instance=application_instance, settings=settings
                )

        return add_courses_with_settings

    @pytest.fixture
    def with_course(self, svc, application_instance, generate_authority_provided_id):
        return factories.Course(
            application_instance=application_instance,
            authority_provided_id=generate_authority_provided_id.return_value,
            lms_id="context_id",
        )

    @pytest.fixture
    def svc(self, db_session, application_instance):
        return CourseService(db=db_session, application_instance=application_instance)

    @pytest.fixture
    def application_instance(self, application_instance):
        application_instance.tool_consumer_instance_guid = "tool_consumer_instance_guid"
        return application_instance

    @pytest.fixture(autouse=True)
    def generate_authority_provided_id(self, patch):
        generate_authority_provided_id = patch(
            "lms.services.course.GroupingService.generate_authority_provided_id"
        )
        generate_authority_provided_id.return_value = "AUTHORITY_PROVIDED_ID"

        return generate_authority_provided_id


class TestCourseServiceFactory:
    def test_it(self, pyramid_request, application_instance_service, CourseService):
        svc = course_service_factory(sentinel.context, pyramid_request)

        application_instance_service.get_current.assert_called_once_with()

        CourseService.assert_called_once_with(
            db=pyramid_request.db,
            application_instance=application_instance_service.get_current.return_value,
        )

        assert svc == CourseService.return_value

    @pytest.fixture
    def CourseService(self, patch):
        return patch("lms.services.course.CourseService")
