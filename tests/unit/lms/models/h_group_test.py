from unittest import mock

import pytest

from lms.models import HGroup


class TestHGroup:
    def test_groupid(self):
        group = HGroup(mock.sentinel.name, "test_authority_provided_id")

        groupid = group.groupid("lms.hypothes.is")

        assert groupid == "group:test_authority_provided_id@lms.hypothes.is"

    @pytest.mark.parametrize(
        "context_parts",
        (
            ["tool_consumer_instance_guid", "context_id"],
            ["tool_consumer_instance_guid", "context_id", "section_id"],
        ),
    )
    def test_from_lti_parts(self, context_parts, hashed_id):
        group = HGroup.from_lti_parts("irrelevant", *context_parts, type_="type_string")

        hashed_id.assert_called_once_with(*context_parts)
        assert group.authority_provided_id == hashed_id.return_value
        assert group.type == "type_string"

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
    def test_from_lti_parts_truncates_the_name(self, name, expected_result):
        group = HGroup.from_lti_parts(name, "irrelevant", "irrelevant")

        assert group.name == expected_result

    @pytest.fixture
    def hashed_id(self, patch):
        return patch("lms.models.h_group.hashed_id")
