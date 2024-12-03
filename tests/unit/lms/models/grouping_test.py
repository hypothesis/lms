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

    def test_get_mapped_file_empty_extra(self):
        course = factories.Course(extra={})

        assert course.get_mapped_file_id("ID") == "ID"

    def test_get_mapped_file_empty_mapping(self):
        course = factories.Course(extra={"course_copy_file_mappings": {}})

        assert course.get_mapped_file_id("ID") == "ID"

    def test_get_mapped_file(self):
        course = factories.Course(
            extra={"course_copy_file_mappings": {"ID": "OTHER_ID"}}
        )

        assert course.get_mapped_file_id("ID") == "OTHER_ID"

    def test_set_mapped_file_id(self):
        course = factories.Course(extra={})

        course.set_mapped_file_id("OLD", "NEW")

        assert course.extra["course_copy_file_mappings"]["OLD"] == "NEW"

    def test_get_mapped_group_set_empty_extra(self):
        course = factories.Course(extra={})

        assert course.get_mapped_group_set_id("ID") == "ID"

    def test_get_mapped_group_set_id_empty_mapping(self):
        course = factories.Course(extra={"course_copy_group_set_mappings": {}})

        assert course.get_mapped_group_set_id("ID") == "ID"

    def test_get_mapped_group_set_id(self):
        course = factories.Course(
            extra={"course_copy_group_set_mappings": {"ID": "OTHER_ID"}}
        )

        assert course.get_mapped_group_set_id("ID") == "OTHER_ID"

    def test_set_mapped_group_set_id(self):
        course = factories.Course(extra={})

        course.set_mapped_group_set_id("OLD", "NEW")

        assert course.extra["course_copy_group_set_mappings"]["OLD"] == "NEW"

    def test_get_mapped_page_id_empty_extra(self):
        course = factories.Course(extra={})

        assert course.get_mapped_page_id("ID") == "ID"

    def test_get_mapped_page_id_empty_mapping(self):
        course = factories.Course(extra={"course_copy_page_mappings": {}})

        assert course.get_mapped_page_id("ID") == "ID"

    def test_get_mapped_page_id(self):
        course = factories.Course(
            extra={"course_copy_page_mappings": {"ID": "OTHER_ID"}}
        )

        assert course.get_mapped_page_id("ID") == "OTHER_ID"

    def test_set_mapped_page_id(self):
        course = factories.Course(extra={})

        course.set_mapped_page_id("OLD", "NEW")

        assert course.extra["course_copy_page_mappings"]["OLD"] == "NEW"
