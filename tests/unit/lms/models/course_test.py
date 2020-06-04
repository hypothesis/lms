from lms.models import Course


class TestCourse:
    def test_settings(self):
        course = Course(_settings={"group": {"key": "value"}})

        settings = course.settings

        assert settings.get("group", "key") == "value"
