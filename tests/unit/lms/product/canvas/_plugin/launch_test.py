import pytest

from lms.product.canvas._plugin.launch import CanvasLaunchPlugin


class TestCanvasLaunchPlugin:
    def test_course_extra(self, plugin):
        assert plugin.course_extra({"custom_canvas_course_id": "ID"}) == {
            "canvas": {"custom_canvas_course_id": "ID"}
        }

    @pytest.fixture
    def plugin(self):
        return CanvasLaunchPlugin()
