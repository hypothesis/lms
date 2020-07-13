import pytest
from pytest import param

from lms.models import HGroup
from tests import factories

GROUP_CONSTRUCTORS = (
    (
        HGroup.course_group,
        ("tool_consumer_instance_guid", "context_id"),
        "course_group",
    ),
    (
        HGroup.section_group,
        ("tool_consumer_instance_guid", "context_id", "section_id"),
        "sections_group",
    ),
)


class TestHGroup:
    def test_groupid(self):
        group = factories.HGroup(authority_provided_id="test_authority_provided_id")

        groupid = group.groupid("lms.hypothes.is")

        assert groupid == "group:test_authority_provided_id@lms.hypothes.is"

    def test_course_group(self, hashed_id):
        group = HGroup.course_group("irrelevant", "tool_guid", "context_id")

        hashed_id.assert_called_once_with("tool_guid", "context_id")
        assert group.authority_provided_id == hashed_id.return_value
        assert group.type == "course_group"

    def test_sections_group(self, hashed_id):
        group = HGroup.section_group(
            "irrelevant", "tool_guid", "context_id", "section_id"
        )

        hashed_id.assert_called_once_with("tool_guid", "context_id", "section_id")
        assert group.authority_provided_id == hashed_id.return_value
        assert group.type == "section_group"

    @pytest.mark.parametrize(
        "name,expected_result",
        (
            (None, None),
            ("Test Course", "Test Course"),
            (" Test Course ", "Test Course"),
            ("Test   Course", "Test   Course"),
            ("Object Oriented Polymorphism 101", "Object Oriented Polymorp…"),
            ("  Object Oriented Polymorphism 101  ", "Object Oriented Polymorp…"),
        ),
    )
    @pytest.mark.parametrize(
        "constructor",
        (
            param(
                lambda name: HGroup.course_group(name, "blah", "blah"),
                id="course_group",
            ),
            param(
                lambda name: HGroup.section_group(name, "blah", "blah", "blah"),
                id="section_group",
            ),
        ),
    )
    def test_contructors_truncate_the_name(self, constructor, name, expected_result):
        group = constructor(name)

        assert group.name == expected_result

    @pytest.fixture
    def hashed_id(self, patch):
        return patch("lms.models.h_group.hashed_id")
