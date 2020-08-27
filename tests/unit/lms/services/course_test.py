import datetime
from unittest.mock import sentinel

import pytest

from lms.models import Course, CourseGroupsExportedFromH
from lms.services.course import course_service_factory
from tests import factories


class TestCourseService:
    @pytest.mark.parametrize("canvas_sections_enabled", [True, False])
    def test_inserting_True_and_False(
        self, ai_getter, db_session, svc, canvas_sections_enabled
    ):
        ai_getter.settings.return_value.set(
            "canvas", "sections_enabled", canvas_sections_enabled
        )

        svc.get_or_create("test_authority_provided_id")

        course = db_session.query(Course).one()
        assert (
            course.settings.get("canvas", "sections_enabled") == canvas_sections_enabled
        )

    def test_it_does_nothing_if_theres_already_a_matching_row(
        self, ai_getter, application_instance, pyramid_request, svc
    ):
        existing_course = factories.Course(
            application_instance=application_instance,
            authority_provided_id="test_authority_provided_id",
            settings={},
        )
        existing_course.settings.set("canvas", "sections_enabled", False)
        ai_getter.settings.return_value.set("canvas", "sections_enabled", True)

        svc.get_or_create("test_authority_provided_id")

        existing_course = pyramid_request.db.query(Course).one()
        assert not existing_course.settings.get("canvas", "sections_enabled")

    @pytest.mark.parametrize("canvas_sections_enabled", [True, False])
    def test_it_inserts_False_if_theres_a_matching_row_in_course_groups_exported_from_h(
        self, ai_getter, db_session, svc, canvas_sections_enabled
    ):
        db_session.add(
            CourseGroupsExportedFromH(
                authority_provided_id="test_authority_provided_id",
                created=datetime.datetime.utcnow(),
            )
        )
        ai_getter.settings.return_value.set(
            "canvas", "sections_enabled", canvas_sections_enabled
        )

        svc.get_or_create("test_authority_provided_id")

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
    def svc(self, pyramid_request):
        return course_service_factory(sentinel.context, pyramid_request)

    @pytest.fixture(autouse=True)
    def application_instance(self, pyramid_request):
        return factories.ApplicationInstance(
            consumer_key=pyramid_request.lti_user.oauth_consumer_key
        )


pytestmark = pytest.mark.usefixtures("ai_getter")
