from datetime import datetime

import pytest

from lms.models import ApplicationSettings, CourseGroupsExportedFromH
from lms.product.canvas._plugin.course_service import CanvasCoursePlugin


class TestCanvasCoursePlugin:
    def test_get_new_course_settings(self, plugin, settings):
        settings = plugin.get_new_course_settings(settings, "no_match")

        assert settings.get("canvas", "sections_enabled")

    def test_get_new_course_settings_with_pre_sections_course(
        self, plugin, settings, pre_sections_course
    ):
        settings = plugin.get_new_course_settings(
            settings, pre_sections_course.authority_provided_id
        )

        assert not settings.get("canvas", "sections_enabled")

    @pytest.fixture
    def pre_sections_course(self, db_session):
        pre_sections = CourseGroupsExportedFromH(
            authority_provided_id="authority_provided_id", created=datetime.utcnow()
        )
        db_session.add(pre_sections)
        return pre_sections

    @pytest.fixture
    def settings(self):
        settings = ApplicationSettings()
        settings.set("canvas", "sections_enabled", True)
        return settings

    @pytest.fixture
    def plugin(self, db_session):
        return CanvasCoursePlugin(db_session)
