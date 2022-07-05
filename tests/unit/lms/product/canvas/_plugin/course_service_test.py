from datetime import datetime
from unittest.mock import sentinel

import pytest
from h_matchers import Any

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

    @pytest.mark.parametrize("value", (None, "something"))
    def test_get_new_course_extra(self, plugin, parsed_params, value):
        if value:
            parsed_params["custom_canvas_course_id"] = value

        assert plugin.get_new_course_extra() == {
            "canvas": {"custom_canvas_course_id": value}
        }

    def test_factory(self, pyramid_request):
        pyramid_request.parsed_params = sentinel.parsed_params
        plugin = CanvasCoursePlugin.factory(sentinel.context, pyramid_request)

        assert plugin == Any.instance_of(CanvasCoursePlugin).with_attrs(
            {
                "_db_session": pyramid_request.db,
                "_parsed_params": pyramid_request.parsed_params,
            }
        )

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
    def parsed_params(self):
        return {}

    @pytest.fixture
    def plugin(self, db_session, parsed_params):
        return CanvasCoursePlugin(db_session, parsed_params)
