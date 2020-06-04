import datetime
from unittest.mock import sentinel

import pytest

from lms.models import ApplicationInstance, Course, CourseGroupsExportedFromH
from lms.services.course import course_service_factory


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
        self, ai_getter, pyramid_request, svc
    ):
        existing_course = Course(
            consumer_key=pyramid_request.lti_user.oauth_consumer_key,
            authority_provided_id="test_authority_provided_id",
            _settings={},
        )
        existing_course.settings.set("canvas", "sections_enabled", False)
        pyramid_request.db.add(existing_course)
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

    @pytest.fixture
    def svc(self, pyramid_request):
        return course_service_factory(sentinel.context, pyramid_request)

    @pytest.fixture(autouse=True)
    def application_instance(self, pyramid_request):
        application_instance = ApplicationInstance(
            consumer_key=pyramid_request.lti_user.oauth_consumer_key,
            shared_secret="test_shared_secret",
            lms_url="test_lms_url",
            requesters_email="test_requesters_email",
        )
        pyramid_request.db.add(application_instance)
        pyramid_request.db.flush()
        return application_instance
