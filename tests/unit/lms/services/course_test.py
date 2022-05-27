import datetime
from unittest.mock import sentinel

import pytest

from lms.models import Course, CourseGroupsExportedFromH
from lms.services.course import course_service_factory
from tests import factories

pytestmark = pytest.mark.usefixtures("application_instance_service")


class TestCourseService:
    @pytest.mark.parametrize("canvas_sections_enabled", [True, False])
    def test_it_inserts_False_if_theres_a_matching_row_in_course_groups_exported_from_h(
        self, application_instance_service, db_session, svc, canvas_sections_enabled
    ):
        db_session.add(
            CourseGroupsExportedFromH(
                authority_provided_id="05e99013c901bd8af9b794f0645c0511dc678298",
                created=datetime.datetime.utcnow(),
            )
        )
        application_instance_service.get_current.return_value.settings.set(
            "canvas", "sections_enabled", canvas_sections_enabled
        )

        svc.upsert("tool_consumer_instance_guid", "context_id", "new course name", {})

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
        course = svc.upsert(
            application_instance.tool_consumer_instance_guid,
            "context_id",
            "new course name",
            {},
        )
        # No new courses created
        assert db_session.query(Course).count() == 1

        # And existing course has been updated
        assert course.lms_name == "new course name"

    def test_upsert_creates_new(self, svc, db_session):
        # Starting with a fresh DB
        assert not db_session.query(Course).count()

        course = svc.upsert(
            "tool_consumer_instance_guid", "context_id", "new course name", {}
        )

        assert db_session.query(Course).count() == 1
        # pylint: disable=protected-access
        assert course.authority_provided_id == svc._generate_authority_provided_id(
            "tool_consumer_instance_guid", "context_id"
        )
        assert course.lms_id == "context_id"

    @pytest.mark.usefixtures("with_course")
    def test_get_by_context_id(self, svc, application_instance):
        course = svc.get_by_context_id(
            application_instance.tool_consumer_instance_guid, "context_id"
        )

        assert course.lms_id == "context_id"
        assert (
            course.application_instance.tool_consumer_instance_guid
            == application_instance.tool_consumer_instance_guid
        )

    def test_generate_authority_provided_id(self, svc):
        assert (
            # pylint: disable=protected-access
            svc._generate_authority_provided_id("tool", "context_id")
            == "bc8f8d2c5de70a0f3975268832174fabecfb32d9"
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
    def with_course(self, svc, application_instance):
        return factories.Course(
            application_instance=application_instance,
            # pylint: disable=protected-access
            authority_provided_id=svc._generate_authority_provided_id(
                application_instance.tool_consumer_instance_guid, "context_id"
            ),
            lms_id="context_id",
        )

    @pytest.fixture
    def svc(self, pyramid_request, application_instance_service, application_instance):
        application_instance_service.get_current.return_value = application_instance
        return course_service_factory(sentinel.context, pyramid_request)
