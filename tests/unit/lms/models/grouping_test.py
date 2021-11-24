import pytest

from lms.models import Course
from tests import factories


class TestCourse:
    def test_groupid(self):
        course = factories.Course(authority_provided_id="test_authority_provided_id")

        groupid = course.groupid("lms.hypothes.is")

        assert groupid == "group:test_authority_provided_id@lms.hypothes.is"

    @pytest.mark.parametrize(
        "name,expected_result",
        (
            ("Test Course", "Test Course"),
            (" Test Course ", "Test Course"),
            ("Test   Course", "Test   Course"),
            ("Object Oriented Polymorphism 101", "Object Oriented Polymorp…"),
            ("  Object Oriented Polymorphism 101  ", "Object Oriented Polymorp…"),
        ),
    )
    def test_name(self, name, expected_result):
        course = Course(lms_name=name)

        assert course.name == expected_result
